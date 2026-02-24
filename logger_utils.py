import logging
import os
from typing import Optional

class LoggerUtil:
    """
    日志工具类，用于打印日志到终端或文件
    """
    
    def __init__(self, name: str = __name__, log_file: str = "log.txt", level: int = logging.INFO):
        """
        初始化日志工具类
        
        Args:
            name: 日志记录器名称
            log_file: 日志文件路径，默认为"log.txt"
            level: 日志级别，默认为INFO
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 创建格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # 创建文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        """
        记录信息级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.info(message)
    
    def debug(self, message: str):
        """
        记录调试级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.debug(message)
    
    def warning(self, message: str):
        """
        记录警告级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.warning(message)
    
    def error(self, message: str):
        """
        记录错误级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.error(message)
    
    def critical(self, message: str):
        """
        记录严重错误级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.critical(message)


def setup_logger(name: str = __name__, log_file: Optional[str] = None, level: int = logging.INFO) -> LoggerUtil:
    """
    创建并返回一个LoggerUtil实例
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，如果为None则使用默认值"log.txt"
        level: 日志级别，默认为INFO
        
    Returns:
        LoggerUtil实例
    """
    if log_file is None:
        log_file = "log.txt"
    
    return LoggerUtil(name=name, log_file=log_file, level=level)


def log_info(logger_instance: LoggerUtil, message: str):
    """
    便捷函数：记录信息级别日志
    
    Args:
        logger_instance: LoggerUtil实例
        message: 日志消息
    """
    logger_instance.info(message)


def log_debug(logger_instance: LoggerUtil, message: str):
    """
    便捷函数：记录调试级别日志
    
    Args:
        logger_instance: LoggerUtil实例
        message: 日志消息
    """
    logger_instance.debug(message)


def log_warning(logger_instance: LoggerUtil, message: str):
    """
    便捷函数：记录警告级别日志
    
    Args:
        logger_instance: LoggerUtil实例
        message: 日志消息
    """
    logger_instance.warning(message)


def log_error(logger_instance: LoggerUtil, message: str):
    """
    便捷函数：记录错误级别日志
    
    Args:
        logger_instance: LoggerUtil实例
        message: 日志消息
    """
    logger_instance.error(message)


def log_critical(logger_instance: LoggerUtil, message: str):
    """
    便捷函数：记录严重错误级别日志
    
    Args:
        logger_instance: LoggerUtil实例
        message: 日志消息
    """
    logger_instance.critical(message)


# 创建一个全局logger实例供其他脚本直接使用
global_logger = setup_logger(name="GlobalLogger", log_file="global_log.txt", level=logging.ERROR)


# 便捷函数，直接使用全局logger
def log_global_info(message: str):
    """
    使用全局logger记录信息级别日志
    
    Args:
        message: 日志消息
    """
    global_logger.info(message)


def log_global_debug(message: str):
    """
    使用全局logger记录调试级别日志
    
    Args:
        message: 日志消息
    """
    global_logger.debug(message)


def log_global_warning(message: str):
    """
    使用全局logger记录警告级别日志
    
    Args:
        message: 日志消息
    """
    global_logger.warning(message)


def log_global_error(message: str):
    """
    使用全局logger记录错误级别日志
    
    Args:
        message: 日志消息
    """
    global_logger.error(message)


def log_global_critical(message: str):
    """
    使用全局logger记录严重错误级别日志
    
    Args:
        message: 日志消息
    """
    global_logger.critical(message)


# 示例使用
if __name__ == "__main__":
    # 创建日志实例
    logger = setup_logger(name="ExampleLogger", log_file="example_log.txt")
    
    # 测试各种日志级别
    log_info(logger, "这是信息日志")
    log_debug(logger, "这是调试日志")
    log_warning(logger, "这是警告日志")
    log_error(logger, "这是错误日志")
    log_critical(logger, "这是严重错误日志")
    
    # 也可以直接使用实例方法
    logger.info("直接使用实例方法记录信息")
    logger.error("直接使用实例方法记录错误")
    
    # 测试全局logger
    print("\n测试全局logger:")
    log_global_info("这是使用全局logger的信息日志")
    log_global_debug("这是使用全局logger的调试日志")
    log_global_warning("这是使用全局logger的警告日志")
    log_global_error("这是使用全局logger的错误日志")
    log_global_critical("这是使用全局logger的严重错误日志")