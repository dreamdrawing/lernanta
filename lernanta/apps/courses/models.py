import simplejson as json
import datetime

from django.utils.translation import ugettext as _

from l10n.urlresolvers import reverse

from drumbeat.utils import slugify
from courses import db
from content2 import models as content_model
from replies import models as comment_model
from learn import models as learn_model

import logging
log = logging.getLogger(__name__)


class ResourceNotFoundException(Exception):
    pass


class DataIntegrityException(Exception):
    pass


def course_uri2id(course_uri):
    return course_uri.strip('/').split('/')[-1]


def course_id2uri(course_id):
    return '/uri/course/{0}/'.format(course_id)


def _get_course_db(course_uri):
    course_id = course_uri2id(course_uri)
    try:
        course_db = db.Course.objects.get(id=course_id)
    except:
        raise ResourceNotFoundException
    return course_db


def get_course(course_uri):
    course_db = _get_course_db(course_uri)
    course = {
        "id": course_db.id,
        "uri": "/uri/course/{0}".format(course_db.id),
        "title": course_db.title,
        "hashtag": course_db.short_title,
        "slug": slugify(course_db.title),
        "description": course_db.plug,
        "language": course_db.language,
    }
    course["draft"] = course_db.draft
    course["archived"] = course_db.archived

    if len(course_db.image_uri) > 0:
        course["image_uri"] = course_db.image_uri

    content = get_course_content(course_uri)
    if len(content) > 0:
        course["about_uri"] = content[0]['uri']
    else:
        log.error("missing about content")
        raise DataIntegrityException

    course["content"] = content[1:]
    return course


def get_courses(title=None, hashtag=None, language=None, organizer_uri=None, draft=None, archived=None):
    results = db.Course.objects
    #NOTE: could also take **kwargs and do results.filter(**kwargs)
    filters = {}
    if title:
        filters['title'] = title
    if hashtag:
        filters['short_title'] = hashtag
    if language:
        filters['language'] = language
    if organizer_uri:
        filters['organizer_uri'] = organizer_uri
    if draft != None:
        filters['draft'] = draft
    if archived != None:
        filters['archived'] = archived
    results = results.filter(**filters)
    return [ get_course(course_id2uri(course_db.id)) for course_db in results ]


def create_course(title, hashtag, description, language, organizer_uri):
    course_db = db.Course(
        title=title,
        short_title=hashtag,
        plug=description,
        language=language
    )

    course_db.save()

    about = content_model.create_content(
       **{"title": _("About"), "content": "", "author_uri": organizer_uri}
    )
    add_course_content("/uri/course/{0}".format(course_db.id), about['uri'])
    create_course_cohort("/uri/course/{0}".format(course_db.id), organizer_uri)
    course = get_course("/uri/course/{0}".format(course_db.id))
    return course


def update_course(course_uri, title=None, hashtag=None, description=None, language=None, image_uri=None):
    # TODO
    course_db = _get_course_db(course_uri)
    if title:
        course_db.title = title
    if hashtag:
        course_db.short_title = hashtag
    if description:
        course_db.plug = description
    if language:
        course_db.language = language
    if image_uri:
        course_db.image_uri = image_uri
    course_db.save()

    if course_db.archived == False and course_db.draft == False:
        try:
            learn_model.update_course_listing(**get_course_learn_api_data(course_uri))
        except:
            pass

    return get_course(course_uri)


def get_course_learn_api_data(course_uri):
    course = get_course(course_uri)

    course_url = reverse(
        'courses_slug_redirect', 
        kwargs={'course_id': course["id"]}
    )
    data_url = reverse('courses_learn_api_data', kwargs={'course_id': course["id"]})

    learn_api_data = {
        "course_url": course_url,
        "title": course['title'],
        "description": course['description'],
        "data_url": data_url,
        "language": course['language'],
        "thumbnail_url": "",
        "tags": get_course_tags(course_uri)
    }
    return learn_api_data


def publish_course(course_uri):
    course_db = _get_course_db(course_uri)
    course_db.draft = False
    course_db.archived = False
    course_db.save()

    learn_model.add_course_listing(**get_course_learn_api_data(course_uri))
    
    course = get_course(course_uri)
    # TODO: Notify interested people in new course
    return course


def archive_course(course_uri):
    course_db = _get_course_db(course_uri)
    course_db.archived = True
    course_db.save()

    course = get_course(course_uri)
    learn_model.remove_course_listing(
        course_url="/courses/{0}/{1}".format(course["id"], course["slug"]),
    )

    return course

def unpublish_course(course_uri):
    course_db = _get_course_db(course_uri)
    course_db.archived = False
    course_db.draft = True
    course_db.save()

    course = get_course(course_uri)
    learn_model.remove_course_listing(
        course_url="/courses/{0}/{1}".format(course["id"], course["slug"]),
    )

    return course

def get_course_content(course_uri):
    content = []
    course_id = course_uri2id(course_uri)
    course_db = _get_course_db(course_uri)
    for course_content_db in course_db.content.order_by('index'):
        content_data = content_model.get_content(course_content_db.content_uri)
        content += [{
            "id": content_data["id"],
            "uri": content_data["uri"],
            "title": content_data["title"],
            "index": course_content_db.index,
        }]
    return content


def add_course_content(course_uri, content_uri):
    course_id = course_uri2id(course_uri)
    course_db = _get_course_db(course_uri)
    next_index = 0
    try:
        next_index = db.CourseContent.objects.filter(course = course_db).order_by('-index')[0].index + 1
    except:
        # TODO
        pass
    course_content_db = db.CourseContent(
        course=course_db,
        content_uri=content_uri,
        index=next_index
    )
    course_content_db.save()


def remove_course_content(course_uri, content_uri):
    course_id = course_uri2id(course_uri)
    course_db = _get_course_db(course_uri)
    course_content_db = course_db.content.get(content_uri=content_uri)
    course_content_db.delete()
    for content in course_db.content.filter(index__gt=course_content_db.index):
        content.index = content.index - 1
        content.save()


def reorder_course_content(content_uri, direction):
    course_content_db = None
    try:
        course_content_db = db.CourseContent.objects.get(content_uri=content_uri)
    except:
        raise ResourceNotFoundException
    new_index = course_content_db.index + 1
    if direction == "UP":
        new_index = course_content_db.index - 1
    if new_index < 1:
        return

    try:
        swap_course_content_db = db.CourseContent.objects.get(
            course=course_content_db.course, index=new_index
        )
    except:
        #TODO
        raise Exception("Internal error")

    swap_course_content_db.index = course_content_db.index
    course_content_db.index = new_index
    swap_course_content_db.save()
    course_content_db.save()


def get_course_tags(course_uri):
    course_db = _get_course_db(course_uri)
    tags_db = db.CourseTags.objects.filter(course=course_db)
    return tags_db.values_list('tag', flat=True)


def add_course_tags(course_uri, tags):
    course_db = _get_course_db(course_uri)

    for tag in tags:
        if not db.CourseTags.objects.filter(course=course_db, tag=tag).exists():
            tag_db = db.CourseTags(course=course_db, tag=tag)
            tag_db.save()


def remove_course_tags(course_uri, tags):
    course_db = _get_course_db(course_uri)

    for tag_db in db.CourseTags.objects.filter(course=course_db, tag__in=tags):
        tag_db.delete()


def create_course_cohort(course_uri, organizer_uri):
    course_db = _get_course_db(course_uri)

    if course_db.cohort_set.count() != 0:
        return None

    cohort_db = db.Cohort(
        course=course_db,
        term=db.Cohort.ROLLING,
        signup=db.Cohort.CLOSED
    )
    cohort_db.save()
    try:
        cohort = get_course_cohort(course_uri)
    except:
        log.error("Could not create new cohort!")
        #TODO raise appropriate exception
        raise
    add_user_to_cohort(cohort["uri"], organizer_uri, db.CohortSignup.ORGANIZER)
    return get_course_cohort(course_uri)


def get_course_cohort_uri( course_uri ):
    course_db = _get_course_db(course_uri)
    return "/uri/cohort/{0}".format(course_db.cohort_set.all().values('id')[0]['id'])
 

def get_course_cohort(course_uri):
    course_db = _get_course_db(course_uri)
    if course_db.cohort_set.count() != 1:
        raise DataIntegrityException
    return get_cohort(
        "/uri/cohort/{0}".format(course_db.cohort_set.all()[0].id))


def _get_cohort_db(cohort_uri):
    cohort_id = cohort_uri.strip('/').split('/')[-1]
    try:
        cohort_db = db.Cohort.objects.get(id=cohort_id)
    except:
        raise ResourceNotFoundException
    return cohort_db


def get_cohort(cohort_uri):
    cohort_db = _get_cohort_db(cohort_uri)

    cohort_data = {
        "uri": "/uri/cohort/{0}".format(cohort_db.id),
        "course_uri": "/uri/course/{0}".format(cohort_db.course.id),
        "term": cohort_db.term,
        "signup": cohort_db.signup,
    }
    #NOTE: fetching course + cohort twice when using get_course_cohort
    #NOTE-Q: does cohort.course.id fetch the course data?

    if cohort_db.term != db.Cohort.ROLLING:
        cohort_data["start_date"] = cohort_db.start_date.date()
        cohort_data["end_date"] = cohort_db.end_date.date()

    cohort_data["users"] = []
    cohort_data["organizers"] = []
    for signup in cohort_db.signup_set.filter(leave_date__isnull=True):
        username = signup.user_uri.strip('/').split('/')[-1]
        cohort_data["users"] += [{
            "username": username, "uri": signup.user_uri, "role": signup.role
        }]
        key = "{0}s".format(signup.role.lower())
        if not key in cohort_data:
            cohort_data[key] = []
        cohort_data[key] += [{
            "username": username, "uri": signup.user_uri, "role": signup.role
        }]

    return cohort_data  


def get_cohort_size( uri ):
    cohort_db = _get_cohort_db(uri)
    return cohort_db.signup_set.filter(leave_date__isnull=True).count()


def update_cohort( uri, term=None, signup=None, start_date=None, end_date=None ):
    cohort_db = _get_cohort_db(uri)

    if term:
        cohort_db.term = term
    if signup:
        cohort_db.signup = signup
    if start_date:
        cohort_db.start_date = start_date
    if end_date:
        cohort_db.end_date = end_date
    cohort_db.save()
    return get_cohort(uri)


def user_in_cohort(user_uri, cohort_uri):
    cohort_db = _get_cohort_db(cohort_uri)
    return cohort_db.signup_set.filter(
        user_uri=user_uri, leave_date__isnull=True).exists()


def is_cohort_organizer(user_uri, cohort_uri):
    cohort_db = _get_cohort_db(cohort_uri)
    return cohort_db.signup_set.filter(
        user_uri=user_uri, leave_date__isnull=True,
        role=db.CohortSignup.ORGANIZER).exists()


def add_user_to_cohort(cohort_uri, user_uri, role):
    cohort_db = _get_cohort_db(cohort_uri)
    if db.CohortSignup.objects.filter(cohort=cohort_db, user_uri=user_uri, leave_date__isnull=True).exists():
        return None
    signup_db = db.CohortSignup(
        cohort=cohort_db,
        user_uri=user_uri,
        role=role
    )

    signup_db.save()
    
    signup = {
        "cohort_uri": cohort_uri,
        "user_uri": user_uri,
        "role": role
    }
    return signup


def remove_user_from_cohort(cohort_uri, user_uri):
    cohort_db = _get_cohort_db(cohort_uri)
    try:
        user_signup_db = cohort_db.signup_set.get(
            user_uri=user_uri, leave_date__isnull=True
        )
    except:
        return False, _("No such user in cohort")

    organizer_count = cohort_db.signup_set.filter(
        role=db.CohortSignup.ORGANIZER,
        leave_date__isnull=True
    ).count() == 1

    if user_signup_db.role == db.CohortSignup.ORGANIZER and organizer_count == 1:
        return False, _("Cannot remove last organizer")

    user_signup_db.leave_date = datetime.datetime.utcnow()
    user_signup_db.save()
    return True, None


def add_comment_to_cohort(comment_uri, cohort_uri, reference_uri):
    #NOTE maybe create comment and update comment reference to simplify use?
    cohort_db = _get_cohort_db(cohort_uri)
    cohort_comment_db = db.CohortComment(
        cohort=cohort_db,
        comment_uri=comment_uri,
        reference_uri=reference_uri
    )

    cohort_comment_db.save()

    #TODO update the reference for the comment to point to this cohort comment
    #NOTE maybe eliminate this psuedo resource by using a combined URI cohort+ref

    return comment_model.get_comment(comment_uri)


def get_cohort_comments(cohort_uri, reference_uri):
    cohort_db = _get_cohort_db(cohort_uri)
    cohort_comments = []
    for cohort_comment in cohort_db.comment_set.filter(reference_uri=reference_uri):
        #NOTE: possible performance problem!!
        comment = comment_model.get_comment(cohort_comment.comment_uri)
        cohort_comments += [comment]
        #yield comment
    return cohort_comments

