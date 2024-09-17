from services.ExclusionAggregator import ExclusionAggregator

class ExclusionManagerService:
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.exclusion_aggregator = ExclusionAggregator()
        self.excluded_dirs = self.settings_manager.get_excluded_dirs()
        self.excluded_files = self.settings_manager.get_excluded_files()

    def get_excluded_dirs(self):
        return self.excluded_dirs

    def get_excluded_files(self):
        return self.excluded_files

    def add_directory(self, directory):
        if directory and directory not in self.excluded_dirs:
            self.excluded_dirs.append(directory)
            return True
        return False

    def add_file(self, file):
        if file and file not in self.excluded_files:
            self.excluded_files.append(file)
            return True
        return False

    def remove_exclusion(self, path):
        if path in self.excluded_dirs:
            self.excluded_dirs.remove(path)
            return True
        elif path in self.excluded_files:
            self.excluded_files.remove(path)
            return True
        return False

    def save_exclusions(self):
        self.settings_manager.update_settings({
            'excluded_dirs': self.excluded_dirs,
            'excluded_files': self.excluded_files
        })

    def get_aggregated_exclusions(self):
        exclusions = {'directories': self.excluded_dirs, 'files': self.excluded_files}
        aggregated = self.exclusion_aggregator.aggregate_exclusions(exclusions)
        return self.exclusion_aggregator.format_aggregated_exclusions(aggregated)

    def get_detailed_exclusions(self):
        return {
            'directories': self.excluded_dirs,
            'files': self.excluded_files
        }