# 2. Creating a New Project

CMA is designed with a project-oriented approach, where you create modules and assemble them into agents within a project. You can choose between two project styles:

1. **CMA Interface Project**: Write module definitions and run them as a single agent using the `coma run` command. This is the simplest way to use CMA.

2. **Python Interface Project**: Write module and agent definitions and run multiple agents using the `python` command. This is the most flexible approach.

## Project Structure

Regardless of the project style, you create a new project by simply making a directory.

### CMA Interface Project Structure

For **CMA Interface Projects**, the directory contains agent subdirectories, each storing the module definitions that comprise that agent:

```
sample_project/    # Project directory
├── agent1/        # Agent directory
│   ├── module1.py # Defines module1
│   ├── module2.py # Defines module2
│   └── module3.py # Defines module3
└── agent2/        # Another agent directory
    ├── module1.py # Defines module1
    ├── module2.py # Defines module2
    └── module3.py # Defines module3
```

### Python Interface Project Structure

For **Python Interface Projects**, the directory contains both module definitions and agent scripts:

```
sample_project/ # Project directory
├── module1.py  # Defines module1
├── module2.py  # Defines module2
├── module3.py  # Defines module3
├── agent1.py   # Defines an agent using modules 1, 2, and 3
└── agent2.py   # Defines another agent using modules 1, 2, and 3
```

## Getting Started

We'll begin with the **CMA Interface Project** style, which is simpler and more straightforward for beginners. If you're already familiar with Python and want more flexibility, you can skip ahead to learn about the **Python Interface Project** style.

## Next Steps

Let's create your first CMA project and start building modules!

<div style="text-align: center; margin: 2rem 0;">
    <a href="../creating-modules" class="indigo-button">
        🚀 Creating Modules (CMA Interface)
    </a>
</div>

<style>
.indigo-button {
    display: inline-block;
    padding: 12px 32px;
    background-color: #3F51B5;
    color: #FFFFFF !important;
    text-decoration: none !important;
    border-radius: 6px;
    font-weight: 600;
    font-size: 16px;
    box-shadow: 0 3px 6px rgba(63, 81, 181, 0.25);
    transition: all 0.2s ease;
    border: none;
}

.indigo-button:hover {
    background-color: #303F9F;
    box-shadow: 0 4px 8px rgba(63, 81, 181, 0.35);
    transform: translateY(-1px);
    color: #FFFFFF !important;
    text-decoration: none !important;
}

.indigo-button:visited {
    color: #FFFFFF !important;
}

.indigo-button:active {
    color: #FFFFFF !important;
}
</style>
