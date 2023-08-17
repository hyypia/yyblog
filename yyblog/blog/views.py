from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from django.contrib.postgres.search import SearchVector, SearchRank, SearchQuery
from django.db.models import Count
from taggit.models import Tag

from .models import Post
from .forms import CommentForm, SearchForm


def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    form = SearchForm()

    # Tag filter
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])

    # Pagination
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get("page", 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(
        request,
        "blog/post/list.html",
        {"posts": posts, "search_form": form, "tag": tag},
    )


def post_detail(request, post, year, month, day):
    post = get_object_or_404(
        Post,
        status=Post.Status.PUBLISHED,
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day,
    )

    # Similar posts list
    post_tags_ids = post.tags.values_list("id", flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count("tags")).order_by(
        "-same_tags", "-publish"
    )[:4]

    # Comments
    comments = post.comments.filter(active=True)
    comment_form = CommentForm()
    search_form = SearchForm()

    return render(
        request,
        "blog/post/detail.html",
        {
            "post": post,
            "similar_posts": similar_posts,
            "comments": comments,
            "comment_form": comment_form,
            "search_form": search_form,
        },
    )


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comments = post.comments.filter(active=True)
    comment = None
    comment_form = CommentForm(data=request.POST)

    if comment_form.is_valid():
        comment = comment_form.save(commit=False)
        comment.post = post
        comment.save()
        comment_form = CommentForm()

    return render(
        request,
        "blog/post/detail.html",
        {
            "post": post,
            "comment_form": comment_form,
            "comment": comment,
            "comments": comments,
        },
    )


def post_search(request):
    search_form = SearchForm()
    query = None
    result = []

    if "query" in request.GET:
        search_form = SearchForm(request.GET)
        if search_form.is_valid():
            query = search_form.cleaned_data["query"]
            search_vector = SearchVector("title", "body")
            search_query = SearchQuery(query)
            search_rank = SearchRank(search_vector, search_query)
            result = (
                Post.published.annotate(search=search_vector, rank=search_rank)
                .filter(search=search_query)
                .order_by("-rank")
            )

    return render(
        request,
        "blog/post/search.html",
        {"search_form": search_form, "query": query, "result": result},
    )
