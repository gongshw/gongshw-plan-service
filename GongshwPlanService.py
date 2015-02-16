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


# 得到当前(日、周、月)计划
@app.route('/plan/<unit>', methods=['GET'])
def get_current_plans(unit):
    return wrap_response(Plan.get_current_plans(unit))


# 添加一个计划
@app.route('/plan/<plan_id>', methods=['PUT', 'POST'])
def add_plan(plan_id):
    print request.data
    plan_to_add = request.get_json()
    if not plan_to_add['id'] == plan_id:
        raise Exception('id in url not matched with id in request body')
    Plan.add_plan(plan_to_add)
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
    db = getattr(g, '_db', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(host='192.168.1.101', port=5000, debug=True)
