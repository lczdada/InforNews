import time
from datetime import datetime, timedelta

from flask import request, render_template, current_app, session, url_for, redirect, g, jsonify, abort

from info import db
from info.common import user_loggin_data
from info.constants import ADMIN_USER_PAGE_MAX_COUNT, ADMIN_NEWS_PAGE_MAX_COUNT, QINIU_DOMIN_PREFIX
from info.models import User, News, Category
from info.modules.admin import admin_blu


# 管理员登录
from info.utils.image_storage import upload_img
from info.utils.response_code import RET, error_map


@admin_blu.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        if user_id and is_admin:  # 免密码登录
            return redirect(url_for('admin.index'))

        return render_template('admin/login.html')

    else:
        # 获取参数
        username = request.form.get('username')
        password = request.form.get('password')
        # 校验参数
        if not all([username, password]):
            return render_template('admin/login.html', errmsg='账号或密码不完整')
        # 判断超级管理员是否存在
        try:
            user = User.query.filter_by(mobile=username, is_admin=True).first()
        except BaseException as e:
            current_app.logger.error(e)
            return render_template('admin/login.html', errmsg='数据库查询失败')
        if not user:
            return render_template('admin/login.html', errmsg='该超级管理员不存在')
        # 判断密码是否正确
        if not user.check_password_hash(password):
            return render_template('admin/login.html', errmsg='密码输入错误')

        session['user_id'] = user.id
        session['is_admin'] = True

        # 跳转页面
        return redirect(url_for('admin.index'))


# 后台首页
@admin_blu.route('/index', methods=['GET', 'POST'])
@user_loggin_data
def index():
    user = g.user
    return render_template('admin/index.html', user=user.to_dict())


# 后台退出
@admin_blu.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return redirect('/')


# 用户统计
@admin_blu.route('/user_count')
def user_count():
    # 用户总数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except BaseException as e:
        current_app.logger.error(e)

    # 月新增
    mon_count = 0
    # 获取本地日期
    t = time.localtime()
    # 构建日期字符串
    date_mon_str = '%d-%02d-01' % (t.tm_year, t.tm_mon)
    # 日期字符串可以转换为日期对象
    date_mon = datetime.strptime(date_mon_str, "%Y-%m-%d")
    try:
        mon_count = User.query.filter(User.is_admin == False, User.create_time >= date_mon).count()
    except BaseException as e:
        current_app.logger.error(e)

    # 日新增
    day_count = 0
    # 构建日期字符串
    date_day_str = '%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)
    # 日期字符串可以转换为日期对象
    date_day = datetime.strptime(date_day_str, "%Y-%m-%d")
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time >= date_day).count()
    except BaseException as e:
        current_app.logger.error(e)

    # 每日登录
    # 构建日期字符串
    # 查询的时间应该>某日0点, 切<次日0点

    active_count = list()
    active_time = list()
    try:
        for i in range(30):
            begin_date = date_day - timedelta(days=i)
            end_date = date_day + timedelta(days=1 - i)
            one_day_count = User.query.filter(User.is_admin == False, User.last_login > begin_date,
                                              User.last_login < end_date).count()
            active_count.append(one_day_count)

            # 将日期对象转换为字符串
            one_day_str = begin_date.strftime("%Y-%m-%d")
            active_time.append(one_day_str)
    except BaseException as e:
        current_app.logger.error(e)
    active_time.reverse()
    active_count.reverse()
    data = {
        'total_count': total_count,
        'mon_count': mon_count,
        'day_count': day_count,
        'active_time': active_time,
        'active_count': active_count
    }

    return render_template('admin/user_count.html', data=data)


# 用户列表
@admin_blu.route('/user_list')
def user_list():
    # 获取参数
    page = request.args.get('p', 1)
    # 校验参数
    try:
        page = int(page)
    except BaseException as e:
        current_app.logger.error(e)
        page = 1  # 如果不合法参数默认为1

    # 取出所有的用户传给前端
    user_list = list()
    total_page = 1

    try:
        pn = User.query.order_by(User.last_login.desc()).paginate(page, ADMIN_USER_PAGE_MAX_COUNT)
        user_list = pn.items
        total_page = pn.pages
    except BaseException as e:
        current_app.logger.error(e)

    user_list = [user.to_admin_dict() for user in user_list]
    data = {
        'cur_page': page,
        'total_page': total_page,
    }

    return render_template('admin/user_list.html', user_list=user_list, data=data)


# 新闻审核
@admin_blu.route('/news_review')
def news_review():
    # 获取参数
    page = request.args.get('p', 1)  #不传则默认为1
    keywords = request.args.get('keywords')
    # 校验参数
    try:
        page = int(page)
    except BaseException as e:
        current_app.logger.error(e)
        page = 1  # 默认为1
    # 设置过条件列表
    filter_list = [News.user_id != None]
    if keywords:
        filter_list.append(News.title.contains(keywords))
    try:
        pn = News.query.filter(*filter_list).paginate(page, ADMIN_NEWS_PAGE_MAX_COUNT)
        news_list = pn.items
        total_page = pn.pages
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    data = {
        'news_list': [news.to_review_dict() for news in news_list],
        'cur_page': page,
        'total_page': total_page
    }

    return render_template('admin/news_review.html', data=data)


# 新闻审核详情
@admin_blu.route('/news_review_detail')
def news_review_detail():
    # 获取参数
    news_id = request.args.get('news_id')
    # 校验参数
    try:
        news_id = int(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 从数据库获取
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    return render_template('admin/news_review_detail.html', news=news.to_dict())


# # 新闻审核详情
# @admin_blu.route('/news_review_detail<int:news_id>')
# def news_review_detail(news_id):
#     # 根据新闻id查询该新闻
#     try:
#         news = News.query.get(news_id)
#     except BaseException as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
#
#     if not news:
#         return abort(404)
#
#     return render_template('admin/news_review_detail.html', news=news.to_dict())

# 新闻审核
@admin_blu.route('/news_review_action', methods=['POST'])
def news_review_action():
    # 获取参数
    action = request.json.get('action')
    news_id = request.json.get('news_id')
    reasons= request.json.get('reason')

    # 校验参数
    if not all([action, news_id]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    try:
        news_id = int(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if action not in ['accept', 'reject']:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not news:
        return jsonify(errno=RET.NODATA, errmsg=error_map[RET.NODATA])
    if action == 'accept':
        news.status = 0

    else:
        news.status = -1
        if not reasons:
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
        news.reason = reasons
    db.session.add(news)

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 新闻编辑列表显示
@admin_blu.route('/news_edit')
def news_edit():
    """
    有分页功能,所以接收p参数
    :return:
    """
    page = request.args.get('p', 1)
    keywords = request.args.get('keywords')
    # 校验参数
    try:
        page = int(page)
    except BaseException as e:
        current_app.logger.error(e)
        page = 1  # 如果传入的参数不合法,则默认为1

    # 获取新闻的pagination对象
    news_list = list()
    total_page = 1
    filter_list = [News.status == 0]
    if keywords:
        filter_list.append(News.title.contains(keywords))
    try:
        pn = News.query.filter(*filter_list).order_by(News.create_time.desc()).paginate(page, ADMIN_NEWS_PAGE_MAX_COUNT)
        news_list = pn.items
        total_page = pn.pages
    except BaseException as e:
        current_app.logger.error(e)

    data = {
        'news_list': [news.to_basic_dict() for news in news_list],
        'cur_page': page,
        'total_page': total_page
    }

    return render_template('admin/news_edit.html', data=data)


# 新闻编辑详情,利用动态url
@admin_blu.route('/news_edit_detail<int:news_id>')
def news_edit_detail(news_id):
    news = News.query.get(news_id)
    if not news:
        return abort(404)
    # 将所有分类查出,并找出该新闻对应的分类
    categories = list()
    try:
        categories = Category.query.all()
    except BaseException as e:
        current_app.logger.error(e)
        return abort(404)
    categories_list = list()
    for category in categories:
        is_select = False
        category_dict = category.to_dict()
        if news.category_id == category.id:
            is_select = True
        category_dict['is_select'] = is_select
        categories_list.append(category_dict)

    if len(categories_list):
        categories_list.pop(0)

    return render_template('admin/news_edit_detail.html', news=news.to_dict(),
                           category_list=categories_list)


# 新闻编辑
@admin_blu.route('/news_edit_submit', methods=['POST'])
def news_edit_submit():
    # 获取参数
    news_id = request.form.get('news_id')
    title = request.form.get('title')
    category_id = request.form.get('category_id')
    digest = request.form.get('digest')
    index_image = request.files.get('index_image')
    content = request.form.get('content')

    # 校验参数
    if not all([title, category_id, digest, index_image, content]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    try:
        news_id = int(news_id)
        category_id = int(category_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 从数据库获取新闻
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 判断新闻是否存在
    if not news or not category_id:
        return jsonify(errno=RET.NODATA, errmsg=error_map[RET.NODATA])

    # 修改新闻
    news.title = title
    news.category_id = category_id
    news.digest = digest
    # 上传图片到第三方
    try:
        img_bytes = index_image.read()
        file_name = upload_img(img_bytes)
        news.index_image_url = QINIU_DOMIN_PREFIX + file_name
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])
    news.content = content
    # 设置过修改自动提交
    db.session.add(news)

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


