from django.test.runner import DiscoverRunner


class VerboseDiscoverRunner(DiscoverRunner):
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        if self.verbosity < 2:
            self.verbosity = 2
        return super().run_tests(test_labels, extra_tests=extra_tests, **kwargs)
