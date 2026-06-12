-- 查看 store 表中的所有数据

-- 查看偏好城市
SELECT namespace, key, value FROM store WHERE namespace = 'users';

-- 查看查询历史
SELECT namespace, key, value FROM store WHERE namespace = 'query_history';

-- 查看所有数据
SELECT namespace, key, value FROM store;