from flask import current_app, jsonify, abort, render_template, session, g, request

from info import db
from info.common import user_loggin_data
from info.constants import CLICK_RANK_MAX_NEWS
from info.models import News, User, Comment, CommentLike
from info.modules.news import news_blu
from info.utils.response_code import RET, error_map


# 新闻详情
@news_blu.route('/<int:news_id>')
@user_loggin_data
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
    # 查询新闻,按照点击量的倒序排序,取前10条
    rank_list = []
    try:
        rank_list = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS)
    except BaseException as e:
        current_app.logger.error(e)
    rank_list = [news.to_dict() for news in rank_list]
    # 将用户信息转换为字典
    is_collected = False
    user = g.user
    if user:
        if news in user.collection_news:
            is_collected = True

    # 将评论信息传送给前端
    try:
        comments = Comment.query.filter_by(news_id=news_id).order_by(Comment.create_time.desc()).all()
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    comments_list = list()
    # 将每一条评论的点赞情况添加给前端
    for comment in comments:
        comment_dict = comment.to_dict()
        is_like = False
        if user:
            if comment in user.like_comments:
                is_like = True
        comment_dict['is_like'] = is_like
        comments_list.append(comment_dict)
    # # 将评论的对象列表转字典
    # comments_list = [comment.to_dict() for comment in comments_list]

    is_followed = False
    if user and news.user:
        if news.user in user.followed:
            is_followed = True

    user = user.to_dict() if user else None  # type:User

    return render_template('news/detail.html', news=news.to_dict(), user=user, rank_list=rank_list,
                           is_collected=is_collected, comments=comments_list, is_followed=is_followed)


# 新闻收藏,是局部刷新,所以只能用前端渲染,
@news_blu.route('/news_collect', methods=['POST'])
@user_loggin_data
def news_collect():
    # 判断用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])

    # 获取参数
    news_id = request.json.get('news_id')
    action = request.json.get('action')
    # 校验参数
    if not all({news_id, action}):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 转换整型
    try:
        news_id = int(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    if action not in ['collect', 'cancel_collect']:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 根据user_id 查询新闻
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    if not news:
        return jsonify(errno=RET.NODATA, errmsg=error_map[RET.NODATA])
    # 根据action执行处理,即将user_id和news_id建立获取取消关系
    if action == 'collect':
        if news not in user.collection_news:
            user.collection_news.append(news)
    else:
        if news in user.collection_news:
            user.collection_news.remove(news)
    # 返回json
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 评论
@news_blu.route('/news_comment', methods=['POST'])
@user_loggin_data
def news_comment():
    # 判断是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])
    # 获取参数
    news_id = request.json.get('news_id')
    comment_content = request.json.get('comment')
    parent_id = request.json.get('parent_id')

    # 校验参数
    if not all([news_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 参数整形
    try:
        news_id = int(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 校验新闻是否存在
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 创建模型对象
    comment = Comment()
    comment.news_id = news.id
    comment.user_id = user.id
    comment.content = comment_content
    if parent_id:

        #判断父评论是否存在
        try:
            parent_comment = Comment.query.filter_by(id=parent_id, news_id=news_id).first()
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
        if not parent_comment:
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
        # 校验参数
        try:
            parent_id = int(parent_id)
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
        comment.parent_id = parent_id

    # 将数据添加到数据库
    try:
        db.session.add(comment)
        db.session.commit()
    except BaseException as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 返回结果给前端

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=comment.to_dict())


# 点赞
@news_blu.route('/comment_like', methods=['POST'])
@user_loggin_data
def comment_like():
    # 判断是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])

    # 获取参数
    comment_id = request.json.get('comment_id')
    action = request.json.get('action')

    # 校验校验参数
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 参数整形
    try:
        comment_id = int(comment_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    if action not in ['add', 'remove']:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 判断评论是否存在
    try:
        comment = Comment.query.get(comment_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 根据action来添加或移除点赞
    if action == 'add':
        if comment not in user.like_comments:
            user.like_comments.append(comment)
            comment.like_count += 1

    else:
        if comment in user.like_comments:
            user.like_comments.remove(comment)
            comment.like_count -= 1

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])
