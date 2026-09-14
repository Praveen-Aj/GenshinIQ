import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.services.stat_engine import StatEngineService

def test_100_determinism():
    print("Testing 100 fresh StatEngineService instances for strict bit-for-bit determinism...")
    
    # 1. First run on instance 0
    engine_0 = StatEngineService()
    baseline_kazuha = engine_0.calculate_build_stats("Kaedehara Kazuha", weapon_name_or_id="Freedom-Sworn", game_version="7.0").model_dump_json()
    baseline_hutao = engine_0.calculate_build_stats("Hu Tao", weapon_name_or_id="Staff of Homa", game_version="7.0").model_dump_json()
    baseline_xiao = engine_0.calculate_build_stats("Xiao", weapon_name_or_id="Primordial Jade Cutter", game_version="7.0").model_dump_json()
    baseline_arle = engine_0.calculate_build_stats("Arlecchino", weapon_name_or_id="Calamity Queller", game_version="7.0").model_dump_json()

    for i in range(1, 101):
        fresh_engine = StatEngineService()
        k_res = fresh_engine.calculate_build_stats("Kaedehara Kazuha", weapon_name_or_id="Freedom-Sworn", game_version="7.0").model_dump_json()
        h_res = fresh_engine.calculate_build_stats("Hu Tao", weapon_name_or_id="Staff of Homa", game_version="7.0").model_dump_json()
        x_res = fresh_engine.calculate_build_stats("Xiao", weapon_name_or_id="Primordial Jade Cutter", game_version="7.0").model_dump_json()
        a_res = fresh_engine.calculate_build_stats("Arlecchino", weapon_name_or_id="Calamity Queller", game_version="7.0").model_dump_json()

        assert k_res == baseline_kazuha, f"Kazuha determinism divergence on iteration {i}!"
        assert h_res == baseline_hutao, f"Hu Tao determinism divergence on iteration {i}!"
        assert x_res == baseline_xiao, f"Xiao determinism divergence on iteration {i}!"
        assert a_res == baseline_arle, f"Arlecchino determinism divergence on iteration {i}!"

    print("SUCCESS: 100/100 fresh instance runs yielded 100% bit-for-bit identical outputs.")

if __name__ == "__main__":
    test_100_determinism()
