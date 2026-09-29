"""Integration tests for ProjectService use cases."""

import pytest

from embedcraft.domain.exceptions import ConfigurationError


def test_create_project_and_prevent_duplicates(test_container):
    with test_container.get_session() as session:
        service = test_container.get_project_service(session)
        p1 = service.create_project(name="Unique Project", description="Testing unique")
        assert p1.name == "Unique Project"

        with pytest.raises(ConfigurationError) as exc_info:
            service.create_project(name="Unique Project", description="Duplicate")
        assert "ya existe" in str(exc_info.value.message)


def test_add_and_list_sources(test_container):
    with test_container.get_session() as session:
        service = test_container.get_project_service(session)
        proj = service.create_project(name="Source Project")

        source = service.add_source(
            project_identifier=proj.name,
            path_or_uri="C:/data/docs",
            name="Manuals",
            recursive=True,
        )
        assert source.name == "Manuals"

        sources = service.list_sources(proj.name)
        assert len(sources) == 1
        assert sources[0].id == source.id
