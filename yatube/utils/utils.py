from django.core.paginator import Paginator


def create_paginator(request, post_list, count_post_in_page):
    paginator = Paginator(post_list, count_post_in_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
