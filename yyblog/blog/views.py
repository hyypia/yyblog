from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from django.contrib.postgres.search import SearchVector, SearchRank, SearchQuery

from .models import Post
from .forms import CommentForm, SearchForm


def post_list(request):
    post_list = Post.published.all()
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get("page", 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(request, "blog/post/list.html", {"posts": posts})


def post_detail(request, post, year, month, day):
    post = get_object_or_404(
        Post,
        status=Post.Status.PUBLISHED,
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day,
    )
    comments = post.comments.filter(active=True)
    form = CommentForm()
    return render(
        request,
        "blog/post/detail.html",
        {"post": post, "comments": comments, "form": form},
    )


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comments = post.comments.filter(active=True)
    comment = None
    form = CommentForm(data=request.POST)

    # FIXME Add auto cleaning form
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()

    return render(
        request,
        "blog/post/detail.html",
        {"post": post, "form": form, "comment": comment, "comments": comments},
    )


def post_search(request):
    form = SearchForm()
    query = None
    result = []

    if "query" in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data["query"]
            search_vector = SearchVector("title", "body")
            search_query = SearchQuery(query)
            result = (
                Post.published.annotate(
                    search=search_vector, rank=SearchRank(search_vector, search_query)
                )
                .filter(search=search_query)
                .order_by("-rank")
            )

    return render(
        request,
        "blog/post/search.html",
        {"form": form, "query": query, "result": result},
    )
