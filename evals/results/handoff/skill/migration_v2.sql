-- Draft only. This adds the new field while preserving the old field.
ALTER TABLE customers ADD COLUMN display_name VARCHAR(255);
UPDATE customers SET display_name = name WHERE display_name IS NULL;
