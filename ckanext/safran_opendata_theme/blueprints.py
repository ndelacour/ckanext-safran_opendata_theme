# encoding: utf-8

from flask import Blueprint

from ckantoolkit import render


blueprint = Blueprint(
    u'publications_qld',
    __name__
)

blueprint.add_url_rule(u'/header.html', 'header', view_func=lambda: render('header.html'))
blueprint.add_url_rule(u'/robots.txt', 'robots', view_func=lambda: render('robots.txt'))
