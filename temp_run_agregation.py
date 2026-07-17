#!/usr/bin/env python3
from pathlib import Path
import runpy

source_path = Path('temp_collect_agregation.py')
text = source_path.read_text(encoding='utf-8')
text = text.replace(
    '    readme = f"""# Agrégation externe de mathématiques — lot {root.name}\\n\\n"\n',
    '    readme = f"# Agrégation externe de mathématiques — lot {root.name}\\n\\n"\n',
)
fixed_path = Path('temp_collect_agregation_fixed.py')
fixed_path.write_text(text, encoding='utf-8')
runpy.run_path(str(fixed_path), run_name='__main__')
