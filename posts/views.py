from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.order_by(
        '-pub_date').select_related('author').select_related('group').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    def_index = True
    return render(request, 'index.html', {'page': page,
                                          'def_index': def_index,
                                          'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).order_by(
        "-pub_date").select_related('author').select_related('group').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    quantity = Post.objects.filter(group=group).count()
    return render(request, "group.html", {"group": group, "page": page,
                                          'paginator': paginator,
                                          'quantity': quantity})


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request, 'new_post.html', {'form': form})
    form = PostForm()
    return render(request, 'new_post.html', {'form': form})


def group_all(request):
    groups = Group.objects.all()
    return render(request, 'group_all.html', {'groups': groups})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author).order_by(
        '-pub_date').select_related('author').select_related('group').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,  author=author).exists()
    quantity = Post.objects.filter(author=author).count()

    return render(request, 'profile.html', {'posts': posts,
                                            'author': author,
                                            'following': following,
                                            'paginator': paginator,
                                            'quantity': quantity})


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author=author, id=post_id)
    quantity = Post.objects.filter(author=author).count()
    form = CommentForm()
    comments = Comment.objects.filter(post=post).order_by('-created').all()
    comments_count = comments.count()
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,  author=author).exists()
    return render(request, 'post.html', {'post': post,
                                         'author': author,
                                         'form': form,
                                         'comments': comments,
                                         'following': following,
                                         'comments_count': comments_count,
                                         'quantity': quantity})


def post_edit(request, username, post_id):
    edited_post = get_object_or_404(Post, id=post_id)
    if edited_post.author != request.user:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=edited_post)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('post', username=username, post_id=post_id)
        return render(request, 'new_post.html', {'form': form})
    return render(request, 'new_post.html', {'form': form,
                                             'post': edited_post})


def page_not_found(request, exception=None):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('post', username=username, post_id=post_id)
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    follow = Follow.objects.filter(user=request.user)
    authors = [item.author for item in follow]
    posts = Post.objects.order_by(
        '-pub_date').filter(author__in=authors).all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    follow_index = True

    return render(request, 'follow_index.html', {'page': page,
                                                 'follow_index': follow_index,
                                                 'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    if author == request.user:
        return redirect('profile', username=username)
    following = Follow.objects.filter(user=request.user,
                                      author=author).exists()
    if not following:
        Follow.objects.create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.get(user=request.user, author=author)
    follow.delete()
    return redirect('profile', username=username)
