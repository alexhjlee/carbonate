import os
import sys

# Inject the graphite libs into the system path
venv_root = ""
if os.environ.get("VIRTUAL_ENV"):
    # Running in a virtual environment
    venv_root = [p for p in sys.path if p.endswith("site-packages")][-1]
sys.path.insert(0, venv_root + "/opt/graphite/lib")

# We're going to use carbon's libs directly to do things
try:
    from carbon import util
    from carbon.aggregator.rules import RuleManager
    from carbon.routers import AggregatedConsistentHashingRouter, ConsistentHashingRouter
except ImportError as e:
    raise SystemExit("No bueno. Can't import carbon! (" + str(e) + ")")


class Cluster():
    def __init__(self, config, cluster='main', aggregation_rules=None):
        relay_method = config.relay_method(cluster=cluster)
        if relay_method == "consistent-hashing":
            self.ring = ConsistentHashingRouter(config.replication_factor(cluster))
        elif relay_method == "aggregated-consistent-hashing":
            if aggregation_rules:
                RuleManager.read_from(aggregation_rules)
            self.ring = AggregatedConsistentHashingRouter(RuleManager, config.replication_factor(cluster))

        try:
            dest_list = config.destinations(cluster)
            self.destinations = util.parseDestinations(dest_list)
        except ValueError as e:
            raise SystemExit("Unable to parse destinations!" + str(e))

        for d in self.destinations:
            self.ring.addDestination(d)

    def getDestinations(self, metric):
        return self.ring.getDestinations(metric)
