from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from yatube.settings import POSTS_PER_PAGE

User = get_user_model()


def posts_paginator(request, posts, per_page):
    """Вспомогательная функция паджинатор формирует page
    для передачи в context в используемых view"""
    paginator = Paginator(posts, per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return page


def index(request):
    posts = Post.objects.select_related('author', 'group').all()
    page = posts_paginator(request, posts, POSTS_PER_PAGE)
    return render(request, 'posts/index.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page = posts_paginator(request, posts, POSTS_PER_PAGE)
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
        {'form': form, 'is_edit': False}
    )


def is_following(user, author):
    """Вспомогательная функция определяет подписан ли
    пользователь на автора записи"""
    if not user.is_authenticated:
        return False
    following = Follow.objects.filter(user=user, author=author).exists()
    return following


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page = posts_paginator(request, posts, POSTS_PER_PAGE)
    following = is_following(request.user, author)
    return render(
        request,
        'posts/profile.html',
        {'author': author, 'page': page,
         'following': following}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm()
    following = is_following(request.user, post.author)
    # TestPostView.test_post_view_get требует комментарии в контексте
    comments = comments = post.comments.all()
    return render(
        request,
        'posts/post.html',
        {'author': post.author, 'post': post, 'comments': comments,
         'form': form, 'following': following},
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
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page = posts_paginator(request, posts, POSTS_PER_PAGE)
    return render(request, 'posts/follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author or is_following(request.user, author):
        return redirect('profile', username)
    Follow.objects.create(user=request.user, author=author)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=user).delete()
    return redirect('profile', username)
