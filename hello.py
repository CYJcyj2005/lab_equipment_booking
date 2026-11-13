"""实验一：验证 Python、编辑器与 Git 工具链的 Hello World 程序。"""


def main() -> None:
    """输出问候语并打印当前 Python 版本信息。"""
    import platform

    print("Hello, World! Lab Equipment Booking - toolchain OK.")
    print(f"Python {platform.python_version()} on {platform.system()}")


if __name__ == "__main__":
    main()
