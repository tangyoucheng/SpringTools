/*
 * Copyright(c) 2011 
 */
package cn.com.platform.framework.common.exception;

/**
 * サービスフレームワーク系统例外。
 * <p>
 * サービスフレームワーク内にて系统例外を生成する場合はこの例外クラスをスローする。
 * </p>
 * 
 * @author t.d.m
 */
public class SystemException extends Exception {

    /**
     * 串行版本号
     */
    private static final long serialVersionUID = 713508944593922816L;

    /**
     * SystemException を構築します。
     */
    public SystemException() {
        super();
    }

    /**
     * 指定された詳細メッセージを示す SystemException を構築します。
     * 
     * @param _message 詳細メッセージ
     */
    public SystemException(String _message) {
        super(_message);
    }

    /**
     * 指定された原因を持つ SystemException を構築します。
     * 
     * @param _throwable 原因
     */
    public SystemException(Throwable _throwable) {
        super(_throwable);
    }

    /**
     * 指定された詳細メッセージと原因を持つ SystemException を構築します。
     * 
     * @param _message 詳細メッセージ
     * @param _throwable 原因
     */
    public SystemException(String _message, Throwable _throwable) {
        super(_message, _throwable);
    }

}
