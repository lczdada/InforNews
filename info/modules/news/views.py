from flask import current_app, jsonify, abort, render_template

from info.models import News
from info.modules.news import news_blu
from info.utils.response_code import RET, error_map


@news_blu.route('/<int:news_id>')
def news_detail(news_id):  # 全局刷新,后端渲染,返回html
    news = None   # type:News
    # 从数据库取出新闻数据
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    if not news:
        return abort(404)

    # 新闻的点击量+1
    news.clicks += 1
    return render_template('news/detail.html', news=news.to_dict())
