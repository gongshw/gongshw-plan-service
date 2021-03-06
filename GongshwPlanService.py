# coding=utf-8
from flask import Flask, request, jsonify, g
from Plan import RequestException
import Plan
import traceback

app = Flask(__name__)


def wrap_response(result):
    return jsonify(result=result, error=None)


def success():
    return wrap_response(True)


# 测试服务器
@app.route('/')
def ping():
    return success()


# 得到计划
@app.route('/plan/<unit>/<int:index>', methods=['GET'])
def get_plans(index, unit):
    return wrap_response(Plan.get_plans(index, unit))


# 得到当前的所有的计划
@app.route('/plan/active', methods=['GET'])
def get_current_plans():
    return wrap_response(Plan.get_current_plans())


# 添加/修改一个计划
@app.route('/plan/<plan_id>', methods=['PUT', 'POST'])
def add_plan(plan_id):
    plan_to_save = request.get_json()
    if not plan_to_save['id'] == plan_id:
        raise Exception('id in url not matched with id in request body')
    plan_exist = Plan.get_plan(plan_id)
    if plan_exist:
        if 'sort' in plan_to_save and type(plan_to_save['sort']) in [float, int]:
            Plan.update_plan_filed(plan_id, 'sort', plan_to_save['sort'])
    else:
        Plan.add_plan(plan_to_save)
    return success()


# 删除一个计划
@app.route('/plan/<plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    Plan.delete_plan(plan_id)
    return success()


# 把一个计划标记为已完成
@app.route('/plan/<plan_id>/<index>/_done', methods=['PUT', 'POST'])
def finish_plan(plan_id, index):
    Plan.add_plan_record(plan_id, index)
    return success()


# 把一个计划标记为以未完成
@app.route('/plan/<plan_id>/<index>/_done', methods=['DELETE'])
def remove_finish_plan(plan_id, index):
    Plan.delete_plan_record(plan_id, index)
    return success()


@app.errorhandler(RequestException)
def request_error_handler(error):
    traceback.print_exc()
    return jsonify({'error': error.message}), 400


@app.teardown_appcontext
def close_connection(e):
    if e is not None:
        print e
    db = getattr(g, '_db', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
