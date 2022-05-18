# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright (c) 2022 ScyllaDB

from sdcm.provision.provisioner import PricingModel, provisioner_factory
from sdcm.sct_provision.instances_provider import provision_sct_resources
from sdcm.test_config import TestConfig


def test_can_provision_instances_according_to_sct_configuration(sct_config, azure_service):
    """Integration test for provisioning sct resources according to SCT configuration."""
    tags = TestConfig.common_tags()
    provision_sct_resources(sct_config=sct_config, azure_service=azure_service)
    provisioner_eastus = provisioner_factory.create_provisioner(
        backend="azure", test_id=sct_config.get("test_id"), region="eastus", azure_service=azure_service)
    eastus_instances = provisioner_eastus.list_instances()
    db_nodes = [node for node in eastus_instances if node.tags['NodeType'] == "db"]
    loader_nodes = [node for node in eastus_instances if node.tags['NodeType'] == "loader"]
    monitor_nodes = [node for node in eastus_instances if node.tags['NodeType'] == "monitor"]

    assert len(db_nodes) == 3
    assert len(loader_nodes) == 2
    assert len(monitor_nodes) == 1
    db_node = db_nodes[0]
    assert db_node.region == "eastus"
    assert list(db_node.tags.keys()) == list(tags.keys()) + ["NodeType", "keepAction"]
    assert db_node.pricing_model == PricingModel.SPOT

    provisioner_easteu = provisioner_factory.create_provisioner(backend="azure", test_id=sct_config.get("test_id"),
                                                                region="easteu", azure_service=azure_service)
    easteu_instances = provisioner_easteu.list_instances()
    db_nodes = [node for node in easteu_instances if node.tags['NodeType'] == "db"]
    loader_nodes = [node for node in easteu_instances if node.tags['NodeType'] == "loader"]
    monitor_nodes = [node for node in easteu_instances if node.tags['NodeType'] == "monitor"]

    assert len(db_nodes) == 1
    assert len(loader_nodes) == 0
    assert len(monitor_nodes) == 0
    db_node = db_nodes[0]
    assert db_node.region == "easteu"
    assert list(db_node.tags.keys()) == list(tags.keys()) + ["NodeType", "keepAction"]
    assert db_node.pricing_model == PricingModel.SPOT


def test_fallback_on_demand_when_spot_fails(fallback_on_demand, sct_config, azure_service):
    # pylint: disable=unused-argument
    provision_sct_resources(sct_config=sct_config, azure_service=azure_service)
    provisioner_eastus = provisioner_factory.create_provisioner(
        backend="azure", test_id=sct_config.get("test_id"), region="eastus", azure_service=azure_service)
    eastus_instances = provisioner_eastus.list_instances()
    db_nodes = [node for node in eastus_instances if node.tags['NodeType'] == "db"]
    loader_nodes = [node for node in eastus_instances if node.tags['NodeType'] == "loader"]
    monitor_nodes = [node for node in eastus_instances if node.tags['NodeType'] == "monitor"]

    assert len(db_nodes) == 3
    assert len(loader_nodes) == 2
    assert len(monitor_nodes) == 1
    for node in db_nodes:
        assert node.pricing_model == PricingModel.ON_DEMAND
    for node in loader_nodes:
        assert node.pricing_model == PricingModel.SPOT
    for node in monitor_nodes:
        assert node.pricing_model == PricingModel.SPOT