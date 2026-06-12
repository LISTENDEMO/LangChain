-- 查看记忆管理后的数据状态

-- 查看 store 表配置信息
SELECT namespace, key, value FROM store;

-- 查看数据库表大小
SELECT name,
       (SELECT COUNT(*) FROM store) as store_count,
       (SELECT COUNT(*) FROM checkpoints) as checkpoints_count,
       (SELECT COUNT(*) FROM writes) as writes_count
FROM sqlite_master WHERE type='table' LIMIT 1;