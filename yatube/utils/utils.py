from django.core.paginator import Paginator


def create_paginator(post_list, count_post_in_page):
    return Paginator(post_list, count_post_in_page)
