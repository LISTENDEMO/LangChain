-- SQLite 查询文件
-- 在 VS Code 中打开此文件，然后按 Ctrl+Shift+E 执行查询

-- 查看所有表
SELECT name FROM sqlite_master WHERE type='table';

-- 查看用户数据 (偏好城市)
SELECT namespace, key, value FROM store WHERE namespace = 'users';

-- 查看查询历史
SELECT namespace, key, value FROM store WHERE namespace = 'query_history';

-- 查看所有用户数据
SELECT * FROM store;