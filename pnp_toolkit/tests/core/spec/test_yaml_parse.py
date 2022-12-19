from pnp_toolkit.core.measures import DistanceMeasure2D
from pnp_toolkit.core.spec.yaml_parse import parse_from_yaml


def test_parse_from_yaml():
    yaml_content = """
    spec_version: "1.0"
    project_name: "yaml parse test case"
    
    variables:
      variable_size: "30*45mm"
    
    documents:
      - name: "test_doc"
        src: ["test_src"]
        paper: "a4"
        pack_strategy: "simple_guillotine"
        output_renderer: "pdf"
        components:
          - name: "test_com"
            size: "{{variable_size}}"
            front_images:
              src: ["sample/path"]
    """

    parsed_spec = parse_from_yaml(yaml_content)

    assert parsed_spec.spec_version == (1, 0)
    assert parsed_spec.project_name == "yaml parse test case"
    assert parsed_spec.variables == {"variable_size": "30*45mm"}

    assert len(parsed_spec.documents) == 1
    for doc in parsed_spec.documents:
        assert doc.name == "test_doc"
        assert doc.src.glob_path == ["test_src"]
        assert doc.paper.name == "a4"
        assert doc.paper.type == "simple"
        assert doc.paper.type_params["size"] == "210*297mm"

        assert len(doc.components) == 1
        for com in doc.components:
            assert com.name == "test_com"
            assert com.size == DistanceMeasure2D.parse_from("30*45mm")
            assert com.front_images.src.glob_path == ["sample/path"]
