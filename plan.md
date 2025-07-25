# Application Improvements Plan

This plan outlines the steps to enhance the roadmap analyzer application with new features and improved data loading capabilities.

## Overview of Changes

1. Rename column "Most likely" to "Likely" and update internal model
2. Add new columns "Start date" and "Priority" (load data only for now)
3. Load items from Excel sheet "Items" instead of default sheet
4. Load configuration from optional "Config" sheet
5. Add quarterly capacity planning from optional "Capacity" sheet

## Phase 1: Model Updates

### Step 1.1: Update WorkItem model field names
- [x] Change `most_likely_estimate` field alias from "Most likely" to "Likely" in `models.py`
- [x] Update all validation error messages referencing "Most likely"
- [x] Update docstrings and comments

### Step 1.2: Add new fields to WorkItem model
- [x] Add `start_date: Optional[datetime]` field with alias "Start date"
- [x] Add `priority: Optional[str]` field with alias "Priority"
- [x] Update model validation and documentation
- [x] Update `__repr__` and `__str__` methods if needed

### Step 1.3: Rename Initiative column to Item
- [x] Change `initiative` field alias from "Initiative" to "Item" in `models.py`
- [x] Update all references throughout the codebase
- [x] Update UI display and examples
- [x] Update required columns in config

## Phase 2: Multi-Sheet Excel Loading

### Step 2.1: Update data loader for "Items" sheet
- [x] Modify `load_project_data()` in `data_loader.py` to read from sheet "Items"
- [x] Add error handling for missing "Items" sheet
- [x] Update function documentation
- [x] Test with existing Excel files

### Step 2.2: Create configuration loading functionality
- [ ] Create `load_config_from_excel()` function in `data_loader.py`
- [ ] Define expected structure for "Config" sheet (key-value pairs)
- [ ] Make it optional - fall back to default config if sheet doesn't exist
- [ ] Integrate with existing `AppConfig` system

### Step 2.3: Create capacity loading functionality
- [ ] Create `CapacityConfig` Pydantic model in `models.py`
- [ ] Create `load_capacity_from_excel()` function in `data_loader.py`
- [ ] Define expected structure for "Capacity" sheet (Quarter, Capacity columns)
- [ ] Make it optional - use default capacity if sheet doesn't exist

## Phase 3: Configuration Integration

### Step 3.1: Update AppConfig model
- [ ] Add `CapacityConfig` to main `AppConfig` model in `config.py`
- [ ] Define default quarterly capacity values
- [ ] Update config validation and documentation

### Step 3.2: Update data loading workflow
- [ ] Modify `load_work_items()` to handle multi-sheet loading
- [ ] Update function signatures to return config and capacity data
- [ ] Ensure backward compatibility with single-sheet files
- [ ] Update error handling and validation

## Phase 4: Application Integration

### Step 4.1: Update main application
- [ ] Modify `main.py` to use new multi-sheet loading functions
- [ ] Update UI to display new fields (Start date, Priority) in data tab
- [ ] Update welcome screen examples to show new column names
- [ ] Test all functionality with new data structure

### Step 4.2: Update simulation and display logic
- [ ] Ensure simulation works with new WorkItem fields
- [ ] Update result display to show new fields where appropriate
- [ ] Update any hardcoded references to "Most likely" column
- [ ] Test simulation with new data structure

## Phase 5: Testing and Validation

### Step 5.1: Create test Excel files
- [ ] Create sample Excel file with "Items", "Config", and "Capacity" sheets
- [ ] Create test file with only "Items" sheet (to test fallbacks)
- [ ] Create test file with old format (to test backward compatibility)

### Step 5.2: End-to-end testing
- [ ] Test complete workflow with new Excel format
- [ ] Verify all existing functionality still works
- [ ] Test error handling for various edge cases
- [ ] Update documentation and README if needed

## Implementation Notes

- **Backward Compatibility**: Ensure existing Excel files still work
- **Error Handling**: Graceful fallbacks when optional sheets are missing
- **Validation**: Proper validation for all new data fields
- **Documentation**: Update all docstrings and comments
- **Testing**: Test each phase before moving to the next

## Expected File Changes

- `src/roadmap_analyzer/models.py` - Update WorkItem and add CapacityConfig
- `src/roadmap_analyzer/data_loader.py` - Add multi-sheet loading functions
- `src/roadmap_analyzer/config.py` - Update AppConfig with capacity settings
- `src/roadmap_analyzer/main.py` - Update UI and data loading calls
- Sample Excel files for testing

## Success Criteria

- [ ] Application loads data from "Items" sheet successfully
- [ ] "Likely" column name is used throughout the application
- [ ] New "Start date" and "Priority" fields are loaded and displayed
- [ ] Optional "Config" sheet loading works with fallback to defaults
- [ ] Optional "Capacity" sheet loading works with fallback to defaults
- [ ] All existing functionality continues to work
- [ ] Proper error messages for missing required sheets/columns

## Phase 2: Multi-Sheet Excel Loading

### Step 2.1: Update data loader for "Items" sheet
- [ ] Modify `load_project_data()` in `data_loader.py` to read from sheet "Items"
- [ ] Add error handling for missing "Items" sheet
- [ ] Update function documentation
- [ ] Test with existing Excel files


### Step 2.3: Create capacity loading functionality
- [ ] Create `CapacityConfig` Pydantic model in `models.py`
- [ ] Create `load_capacity_from_excel()` function in `data_loader.py`
- [ ] Define expected structure for "Capacity" sheet (Quarter, Capacity columns)
- [ ] Make it optional - use default capacity if sheet doesn't exist

## Phase 3: Configuration Integration

### Step 3.1: Update AppConfig model
- [ ] Add `CapacityConfig` to main `AppConfig` model in `config.py`
- [ ] Define default quarterly capacity values
- [ ] Update config validation and documentation

### Step 3.2: Update data loading workflow
- [ ] Modify `load_work_items()` to handle multi-sheet loading
- [ ] Update function signatures to return config and capacity data
- [ ] Ensure backward compatibility with single-sheet files
- [ ] Update error handling and validation

## Phase 4: Application Integration

### Step 4.1: Update main application
- [ ] Modify `main.py` to use new multi-sheet loading functions
- [ ] Update UI to display new fields (Start date, Priority) in data tab
- [ ] Update welcome screen examples to show new column names
- [ ] Test all functionality with new data structure

### Step 4.2: Update simulation and display logic
- [ ] Ensure simulation works with new WorkItem fields
- [ ] Update result display to show new fields where appropriate
- [ ] Update any hardcoded references to "Most likely" column
- [ ] Test simulation with new data structure

### Phase 5: Create configuration loading functionality
- [ ] Create `load_config_from_excel()` function in `data_loader.py`
- [ ] Define expected structure for "Config" sheet (key-value pairs)
- [ ] Make it optional - fall back to default config if sheet doesn't exist
- [ ] Integrate with existing `AppConfig` system

## Phase 6: Testing and Validation

### Step 6.1: Create test Excel files
- [ ] Create sample Excel file with "Items", "Config", and "Capacity" sheets
- [ ] Create test file with only "Items" sheet (to test fallbacks)
- [ ] Create test file with old format (to test backward compatibility)

### Step 6.2: End-to-end testing
- [ ] Test complete workflow with new Excel format
- [ ] Verify all existing functionality still works
- [ ] Test error handling for various edge cases
- [ ] Update documentation and README if needed

## Implementation Notes

- **Backward Compatibility**: Ensure existing Excel files still work
- **Error Handling**: Graceful fallbacks when optional sheets are missing
- **Validation**: Proper validation for all new data fields
- **Documentation**: Update all docstrings and comments
- **Testing**: Test each phase before moving to the next

## Expected File Changes

- `src/roadmap_analyzer/models.py` - Update WorkItem and add CapacityConfig
- `src/roadmap_analyzer/data_loader.py` - Add multi-sheet loading functions
- `src/roadmap_analyzer/config.py` - Update AppConfig with capacity settings
- `src/roadmap_analyzer/main.py` - Update UI and data loading calls
- Sample Excel files for testing

## Success Criteria

- [ ] Application loads data from "Items" sheet successfully
- [ ] "Likely" column name is used throughout the application
- [ ] New "Start date" and "Priority" fields are loaded and displayed
- [ ] Optional "Config" sheet loading works with fallback to defaults
- [ ] Optional "Capacity" sheet loading works with fallback to defaults
- [ ] All existing functionality continues to work
- [ ] Proper error messages for missing required sheets/columns