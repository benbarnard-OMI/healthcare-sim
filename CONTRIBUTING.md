# Contributing to Synthetic Care Pathway Simulator

We welcome contributions to the Synthetic Care Pathway Simulator project! By contributing, you can help improve the project and make it more useful for everyone. Please follow the guidelines below to ensure a smooth and effective contribution process.

## How to Contribute

### 1. Fork the Repository

If you are new to contributing to open-source projects, the first step is to fork the repository. This will create a copy of the project under your GitHub account.

1. Go to the [project repository](https://github.com/benbarnard-OMI/healthcare-sim).
2. Click the "Fork" button in the top-right corner of the page.

### 2. Create a New Branch

Before making any changes, create a new branch for your feature or bugfix. This helps keep your work organized and makes it easier to submit a pull request.

1. Open your terminal or command prompt.
2. Navigate to your forked repository.
3. Create a new branch:
   ```
   git checkout -b my-feature-branch
   ```

### 3. Make Your Changes

Make the necessary changes to the codebase. Ensure that your code follows the project's coding standards and includes appropriate tests.

### 4. Commit Your Changes

Once you have made your changes, commit them with clear and descriptive commit messages.

1. Stage your changes:
   ```
   git add .
   ```
2. Commit your changes:
   ```
   git commit -m "Add feature: description of the feature"
   ```

### 5. Push Your Changes

Push your changes to your forked repository.

1. Push your branch:
   ```
   git push origin my-feature-branch
   ```

### 6. Create a Pull Request

Submit a pull request to the main repository.

1. Go to the [main repository](https://github.com/benbarnard-OMI/healthcare-sim).
2. Click the "New pull request" button.
3. Select your branch from the "compare" dropdown.
4. Provide a clear and descriptive title and description for your pull request.
5. Click "Create pull request".

### 7. Respond to Feedback

Your pull request will be reviewed by the project maintainers. Be prepared to make additional changes based on their feedback. Once your pull request is approved, it will be merged into the main repository.

## Coding Standards

To ensure consistency and readability, please follow these coding standards:

- Use meaningful variable and function names.
- Write clear and concise comments to explain complex logic.
- Follow the PEP 8 style guide for Python code.
- Add type hints to all functions and methods.
- Write unit tests for new features and bug fixes.

## Running Unit Tests

Before submitting your pull request, make sure all tests pass. To run the unit tests, use the following command:
```
pytest
```

This will discover and run all the tests in the `tests` directory.

## Reporting Issues

If you encounter any issues or have suggestions for improvements, please open an issue on the [GitHub repository](https://github.com/benbarnard-OMI/healthcare-sim/issues).

Thank you for contributing to the Synthetic Care Pathway Simulator project!
