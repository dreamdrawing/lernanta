from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^css/$', 'schools.views.multiple_school_css', name='multiple_schools_css'),
    url(r'^(?P<slug>[\w-]+)/$', 'schools.views.home', name='school_home'),
    url(r'^(?P<slug>[\w-]+)/css/$', 'schools.views.school_css', name='schools_css'),
    url(r'^(?P<slug>[\w-]+)/edit/$', 'schools.views.edit', name='schools_edit'),
    url(r'^(?P<slug>[\w-]+)/edit/styles/$', 'schools.views.edit_styles',
      name='schools_edit_styles'),
    url(r'^(?P<slug>[\w-]+)/edit/logo/$', 'schools.views.edit_logo',
      name='schools_edit_logo'),
    url(r'^(?P<slug>[\w-]+)/edit/ajax_logo/$', 'schools.views.edit_logo_async',
      name='schools_edit_logo_async'),
    url(r'^(?P<slug>[\w-]+)/edit/groups_icon/$', 'schools.views.edit_groups_icon',
      name='schools_edit_groups_icon'),
    url(r'^(?P<slug>[\w-]+)/edit/ajax_groups_icon/$', 'schools.views.edit_groups_icon_async',
      name='schools_edit_groups_icon_async'),
    url(r'^(?P<slug>[\w-]+)/edit/background/$', 'schools.views.edit_background',
      name='schools_edit_background'),
    url(r'^(?P<slug>[\w-]+)/edit/ajax_background/$', 'schools.views.edit_background_async',
      name='schools_edit_background_async'),
    url(r'^(?P<slug>[\w-]+)/edit/site_logo/$', 'schools.views.edit_site_logo',
      name='schools_edit_site_logo'),
    url(r'^(?P<slug>[\w-]+)/edit/ajax_site_logo/$', 'schools.views.edit_site_logo_async',
      name='schools_edit_site_logo_async'),
    url(r'^(?P<slug>[\w-]+)/edit/organizers/$',
      'schools.views.edit_organizers',
      name='schools_edit_organizers'),
    url(r'^(?P<slug>[\w-]+)/edit/organizers/matching_non_organizers/$',
      'schools.views.matching_non_organizers',
      name='matching_non_organizers'),
    url(r'^(?P<slug>[\w-]+)/edit/featured/$',
      'schools.views.edit_featured',
      name='schools_edit_featured'),
    url(r'^(?P<slug>[\w-]+)/edit/featured/(?P<project_slug>[\w-]+)/delete/$',
      'schools.views.edit_featured_delete',
      name='schools_edit_featured_delete'),
    url(r'^(?P<slug>[\w-]+)/edit/featured/matching_non_featured/$',
      'schools.views.matching_non_featured',
      name='matching_non_featured'),
    url(r'^(?P<slug>[\w-]+)/edit/declined/$',
      'schools.views.edit_declined',
      name='schools_edit_declined'),
    url(r'^(?P<slug>[\w-]+)/edit/declined/(?P<project_slug>[\w-]+)/delete/$',
      'schools.views.edit_declined_delete',
      name='schools_edit_declined_delete'),
    url(r'^(?P<slug>[\w-]+)/edit/declined/matching_non_declined/$',
      'schools.views.matching_non_declined',
      name='matching_non_declined'),
)
