"""ThaiTravel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from Search import views as search_view
from Discover import views as discover_view
from Person import views as person_view
import settings

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'search/home', search_view.home, name='search_home'),
    url(r'search/search', search_view.search, name='search_search'),
    url(r'search/get_comments', search_view.get_scene_comments, name='search_get_comments'),
    url(r'search/get_scene_list', search_view.get_scene_list, name='search_get_scene_list'),
    url(r'search/hotsearch', search_view.hot_search, name='hot_search'),
    url(r'discover/get_travel_note_list', discover_view.get_travel_note_list, name='travel_note_list'),
    # url(r'discover/travelnote', discover_view.to_travel_note, name='travel_note'),
    url(r'discover/get_travel_note', discover_view.get_travel_note, name='get_travel_note'),
    url(r'discover/search_notes', discover_view.search_notes, name='get_travel_note'),
    url(r'search/get_translate', search_view.get_translation, name='get_translation'),
    url(r'person/login', person_view.login, name='login'),
    url(r'person/register', person_view.register, name='register'),
    # url(r'^hello/', search_view.hello, name='search_hello'),
    url(r'^static/(?P<path>.*)$','django.views.static.serve',{'document_root':settings.STATIC_URL}),
]
