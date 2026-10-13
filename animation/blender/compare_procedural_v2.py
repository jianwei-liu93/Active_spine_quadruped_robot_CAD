"""Reuse the finite surface comparison at the v2 leg extrema."""
import compare_procedural as comparison
comparison.MANIFEST=comparison.ROOT/'animation/geometry/r10/procedural_examples_v2/manifest.json'
comparison.TIMELINE=comparison.ROOT/'animation/motion/coordinated_spine_legs_v2_r10.jsonl.gz'
comparison.REPORT=comparison.ROOT/'reports/animation/procedural_surface_comparison_v2.json'
comparison.SAMPLE_INDICES=(15,165)
comparison.main()
