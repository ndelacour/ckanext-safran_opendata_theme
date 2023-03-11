# encoding: utf-8

import datetime
import re

from ckan import model, plugins
from ckan.plugins.toolkit import add_resource, add_public_directory, \
    add_template_directory, c, config, check_ckan_version, get_action, request

from . import blueprints


def get_gtm_code():
    # To get Google Tag Manager Code
    gtm_code = config.get('ckan.google_tag_manager.gtm_container_id', False)
    return str(gtm_code)


def get_year():
    now = datetime.datetime.now()
    return now.year


def ytp_comments_enabled():
    return "ytp_comments" in config.get('ckan.plugins', False)


def is_datarequests_enabled():
    return "datarequests" in config.get('ckan.plugins', False)


def get_all_groups():
    groups = get_action('group_list')(
        data_dict={'include_dataset_count': False, 'all_fields': True})
    pkg_group_ids = set(group['id'] for group
                        in c.pkg_dict.get('groups', []))
    return [[group['id'], group['display_name']]
            for group in groups if
            group['id'] not in pkg_group_ids]


def get_comment_notification_recipients_enabled():
    return config.get('ckan.comments.follow_mute_enabled', False)


def is_reporting_enabled():
    return 'data_qld_reporting' in config.get('ckan.plugins', '')


def is_request_for_resource():
    """
    Searching for a url path for /dataset/ and /resource/
    eg. /dataset/example/resource/b33a702a-f162-44a8-aad9-b9e630a8f56e
    :return:
    """
    if request:
        path = request.path
        if hasattr(request, 'environ'):
            original_request = request.environ.get('pylons.original_request')
            if original_request:
                path = original_request.path
        return re.search(r"/dataset/\S+/resource/\S+", path)
    return False


# this ensures external css/js is loaded from external staging
# if running in cicd/pdev environments.
def set_external_resources():
    environment = config.get('ckan.site_url', '')
    if 'data.qld' in environment:
        return ''
    else:
        return '//www.data.qld.gov.au'


def is_prod():
    environment = config.get('ckan.site_url', '')
    if 'training' in environment:
        return False
    elif 'dev' in environment:
        return False
    elif 'staging' in environment:
        return False
    elif 'ckan' in environment:
        return False
    else:
        return True


def set_background_image_class():
    environment = config.get('ckan.site_url', '')
    if 'training' in environment:
        background_class = 'qg-training'
    elif 'dev' in environment:
        background_class = 'qg-dev'
    elif 'staging' in environment:
        background_class = 'qg-staging'
    elif 'ckan' in environment:
        background_class = 'qg-dev'
    else:
        background_class = ''
    return background_class


def latest_revision(resource_id):
    resource_revisions = model.Session.query(model.resource_revision_table)\
        .filter(model.ResourceRevision.id == resource_id,
                model.ResourceRevision.expired_timestamp > '9999-01-01')
    highest_value = None
    for revision in resource_revisions:
        if highest_value is None or revision.revision_timestamp > \
                highest_value.revision_timestamp:
            highest_value = revision
    return highest_value


def populate_revision(resource):
    if 'revision_timestamp' in resource \
            or is_ckan_29():
        return
    current_revision = latest_revision(resource['id'])
    if current_revision is not None:
        resource['revision_timestamp'] = current_revision.revision_timestamp


def unreplied_comments_x_days(thread_url):
    """A helper function for Data.Qld Engagement Reporting
    to highlight un-replied comments after x number of days.
    (Number of days is a constant in the reporting plugin)
    """
    comment_ids = []

    if 'data_qld_reporting' in config.get('ckan.plugins', False):
        unreplied_comments = get_action(
            'comments_no_replies_after_x_days'
        )({}, {'thread_url': thread_url})

        comment_ids = [comment[1] for comment in unreplied_comments]

    return comment_ids


def is_ckan_29():
    """
    Returns True if using CKAN 2.9+, with Flask and Webassets.
    Returns False if those are not present.
    """
    return check_ckan_version(min_version='2.9.0')


class PublicationsQldThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    if is_ckan_29():
        plugins.implements(plugins.IBlueprint)

    # IConfigurer

    def update_config(self, config_):
        add_template_directory(config_, 'templates')
        add_public_directory(config_, 'public')
        add_resource('assets', 'publications_qld_theme')

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_gtm_container_id': get_gtm_code,
            'get_year': get_year,
            'ytp_comments_enabled': ytp_comments_enabled,
            'is_datarequests_enabled': is_datarequests_enabled,
            'get_all_groups': get_all_groups,
            'is_request_for_resource': is_request_for_resource,
            'set_background_image_class': set_background_image_class,
            'set_external_resources': set_external_resources,
            'is_prod': is_prod,
            'comment_notification_recipients_enabled':
                get_comment_notification_recipients_enabled,
            'populate_revision': populate_revision,
            'unreplied_comments_x_days': unreplied_comments_x_days,
            'is_reporting_enabled': is_reporting_enabled,
            'is_ckan_29': is_ckan_29,
        }

    # IBlueprint

    def get_blueprint(self):
        return blueprints.blueprint
