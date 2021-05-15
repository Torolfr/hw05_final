from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import POSTS_PER_PAGE

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, POSTS_PER_PAGE, orphans=3)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/index.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, POSTS_PER_PAGE, orphans=3)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'posts/group.html',
        {'group': group, 'page': page}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(
        request,
        'posts/new_post.html',
        {'form': form}
    )


def is_following(user, author):
    following = False
    if not user.is_authenticated:
        return following
    if not Follow.objects.filter(user=user, author=author).exists():
        return following
    following = True
    return following


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = is_following(request.user, author)
    following = True
    posts_count = author.posts.count()
    return render(
        request,
        'posts/profile.html',
        {'author': author, 'page': page,
         'posts_count': posts_count, 'following': following}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id, )
    author = post.author
    posts_count = author.posts.count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    following = is_following(request.user, author)
    return render(
        request,
        'posts/post.html',
        {'author': author, 'post': post, 'posts_count': posts_count,
         'comments': comments, 'form': form, 'following': following},
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != post.author:
        return redirect('post', username, post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('post', username, post_id)
    return render(
        request,
        'posts/new_post.html',
        {'form': form, 'is_edit': True, 'post': post}
    )


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        post = get_object_or_404(Post, id=post_id, author__username=username)
        comment.post = post
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    subs = Follow.objects.filter(user=request.user)
    authors = []
    for sub in subs:
        authors.append(sub.author)
    post_list = Post.objects.filter(author__in=authors)
    paginator = Paginator(post_list, POSTS_PER_PAGE, orphans=3)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    if request.user == author:
        return redirect('profile', username)
    if Follow.objects.filter(user=request.user, author=author).exists():
        return redirect('profile', username)
    Follow.objects.create(user=request.user, author=author)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    user = User.objects.get(username=username)
    Follow.objects.filter(user=request.user, author=user).delete()
    return redirect('profile', username)
