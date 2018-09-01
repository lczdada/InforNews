from datetime import datetime

from info import db

from info.common import user_loggin_data
from info.constants import USER_COLLECTION_MAX_NEWS, QINIU_DOMIN_PREFIX
from info.models import User, tb_user_collection, Category, News
from info.modules.user import user_blu
from flask import render_template, jsonify, g, abort, redirect, request, current_app

from info.utils.image_storage import upload_img
from info.utils.response_code import RET, error_map


# 用户信息
@user_blu.route('/user_info')
@user_loggin_data
def user_info():
    user = g.user
    if not user:
        return redirect('/')
    user = user.to_dict()
    return render_template('news/user.html', user=user)


# 基本信息
@user_blu.route('/base_info', methods=['GET', 'POST'])
@user_loggin_data
def base_info():
    user =g.user   # type:User
    if not user:
        return abort(404)
    if request.method == 'GET':
        return render_template('news/user_base_info.html', user=user)
    else:
        # 获取参数
        signature = request.json.get('signature')
        nick_name = request.json.get('nick_name')
        gender = request.json.get('gender')
        # 校验参数
        if not all([signature, nick_name, gender]):
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
        if gender not in ['MAN', 'WOMAN']:
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

        # 替换数据
        user.signature = signature
        user.nick_name = nick_name
        user.gender = gender

        return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 图片信息
@user_blu.route('/pic_info', methods=['GET', 'POST'])
@user_loggin_data
def pic_info():
    # 判断是否登录
    user = g.user
    if not user:
        return abort(404)
    if request.method == 'GET':
        return render_template('news/user_pic_info.html', user=user.to_dict())
    else:
        # 获取图片
        try:
            img_bytes = request.files.get('avatar').read()
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
        # 上传至第三方服务器
        try:
            file_name = upload_img(img_bytes)
            print(file_name)
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])

        # 修改用户的头像url
        user.avatar_url = file_name
        return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=user.to_dict())


# 修改密码
@user_blu.route('/pass_info', methods=['GET', 'POST'])
@user_loggin_data
def pass_info():
    user = g.user
    if not user:
        return abort(404)
    if request.method == 'GET':
        return render_template('news/user_pass_info.html', user=user.to_dict())
    # POST处理
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')
    if not all([classmethod, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 校验密码是否正确
    if not user.check_password_hash(old_password):
        return jsonify(errno=RET.PWDERR, errmsg=error_map[RET.PWDERR])

    # 修改密码
    user.password = new_password

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 我的收藏
@user_blu.route('/collection')
@user_loggin_data
def collection():
    user = g.user
    if not user:
        return abort(404)
    # 获取参数
    page = request.args.get('p', 1)
    # 校验参数
    try:
        page = int(page)
    except BaseException as e:
        current_app.logger.error(e)
        page = 1  # 如果传入参数有误,默认为1

    # 将当前用户的所有收藏传入模板中
    news_list = []
    total_page = 1
    try:
        pn = user.collection_news.order_by(tb_user_collection.c.create_time.desc()).paginate(page, USER_COLLECTION_MAX_NEWS)
        news_list = pn.items
        total_page = pn.pages
    except BaseException as e:
        current_app.logger.error(e)

    data = {
        'news_list': [news.to_dict() for news in news_list],
        "cur_page": page,
        'total_page': total_page
    }

    return render_template('news/user_collection.html', data=data)


# 发布新闻
@user_blu.route('/news_release', methods=['GET', 'POST'])
@user_loggin_data
def news_release():
    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(404)

    if request.method == 'GET':
        categories = list()
        try:
            categories = Category.query.all()  # type:Category
            categories.pop(0)
        except BaseException as e:
            current_app.logger.error(e)
        return render_template('news/user_news_release.html', categories=categories)  #
    # POST
    else:
        # 获取参数
        title = request.form.get('title')
        digest = request.form.get('digest')
        category_id = request.form.get('category_id')
        index_image = request.files.get('index_image')  # type:FileStorages
        content = request.form.get('content')
        # 校验参数
        if not all([title, digest, content, category_id]):
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
        try:
            category_id = int(category_id)
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

        # 将数据存入数据库
        news = News()
        news.title = title
        news.digest = digest
        news.source = '个人发布'
        news.category_id = category_id
        news.create_time = datetime.now()
        news.status = 1
        news.content = content
        news.user_id =user.id
        if index_image:
            # 将照片存入第三方平台
            index_image = index_image.read()  #
            try:
                files_name = upload_img(index_image)
            except BaseException as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])
            news.index_image_url = QINIU_DOMIN_PREFIX + files_name
        try:
            db.session.add(news)
            db.session.commit()
        except BaseException as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

        # 返回json
        return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 新闻列表
@user_blu.route('/news_list')
@user_loggin_data
def news_list():
    user = g.user   # type:User
    if not user:
        return abort(404)
    # 获取参数
    page = request.args.get('p', 1)
    # 校验参数
    try:
        page = int(page)
    except BaseException as e:
        current_app.logger.error(e)
        page = 1  # 如果传入参数有误,默认为1

    # 将当前用户的所有新闻传入模板中
    news_list = list()
    total_page = 1
    try:
        pn = user.news_list.order_by(News.create_time.desc()).paginate(page, USER_COLLECTION_MAX_NEWS)
        news_list = pn.items
        total_page = pn.pages
    except BaseException as e:
        current_app.logger.error(e)
    data = {
        "news_list": [news.to_review_dict() for news in news_list],
        "cur_page": page,
        "total_page": total_page
    }
    return render_template('news/user_news_list.html', data=data)


# 我的关注
@user_blu.route('/user_follow')
@user_loggin_data
def user_follow():
    # 判断是否登录
    user = g.user
    if not user:
        return abort(404)
    page = request.args.get('p', 1)
    try:
        page = int(page)
    except BaseException as e:
        current_app.logger.error(e)
        page = 1

    # 将当前用户关注的所有人传入模板中
    author_list = list()
    total_page = 1
    try:
        pn = user.followed.paginate(page, USER_COLLECTION_MAX_NEWS)
        author_list = pn.items
        total_page = pn.pages
    except BaseException as e:
        current_app.logger.error(e)

    data = {
        'author_list': [author.to_dict() for author in author_list],
        'cur_page': page,
        "total_page": total_page
    }

    return render_template('news/user_follow.html', data=data)


# 作者详情
@user_blu.route('/author_detail/<int:author_id>')
@user_loggin_data
def author_detail(author_id):
    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(404)
    # 获取参数
    page = request.args.get('p', 1)
    # 校验参数
    try:
        page = int(page)
    except BaseException as e:
        current_app.logger.error(e)
        page = 1  # 参数不合格则默认为1

    # 从数据库查找该作者信息
    author = None
    try:
        author = User.query.get(author_id)
    except BaseException as e:
        current_app.logger.error(e)
    if not author:
        return abort(404)

    # 从数据库查找该作者的所有文章
    news_list = list()
    total_page = 1
    try:
        pn = author.news_list.paginate(page, USER_COLLECTION_MAX_NEWS)
        news_list = pn.items
        total_page = pn.pages
    except BaseException as e:
        current_app.logger.error(e)

    data = {
        'news_list': [news.to_basic_dict() for news in news_list],
        'total_page': total_page,
        'cur_page': page
    }
    # 信息传递给前端
    return render_template('news/other.html', author=author.to_dict(), user=user.to_dict(), news_list=news_list, data=data)