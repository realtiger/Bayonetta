from importlib import import_module
from pathlib import Path

from oracle.sqlalchemy import sql_helper


def scan_all_models(path: Path, prefix: str):
    for p in path.iterdir():
        # 如果是 models.py 文件则导入
        if p.is_file() and p.name == 'models.py':
            import_module(f'{prefix}.{p.stem}')
        elif p.is_dir():
            # 如果是 models 目录则导入该目录下的所有 py 文件
            if p.name == 'models':
                for m in p.iterdir():
                    if m.is_file():
                        import_module(f'{prefix}.models.{m.stem}')

            # 否则如果是目录则递归扫描
            else:
                scan_all_models(p, f'{prefix}.{p.stem}')


# 扫描 apps 下的所有目录下的 models 并导入
scan_all_models(Path(__file__).parent / 'apps', prefix='apps')

__all__ = ["sql_helper"]
