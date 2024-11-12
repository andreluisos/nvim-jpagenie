<div align="center">

# Java Genie

##### Bringing joy to Java programming on Neovim

[![Lua](https://img.shields.io/badge/Lua-blue.svg?style=for-the-badge&logo=lua)](http://www.lua.org)
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](http://www.python.org)
[![Neovim](https://img.shields.io/badge/Neovim%200.9+-blue.svg?style=for-the-badge&logo=neovim)](https://neovim.io)

<img alt="Nvim's Java-Genie" height="280" src="https://github.com/andreluisos/nvim-javagenie/blob/media/logo.png" />
</div>

# Introduction

**nvim-javagenie** is a Neovim plugin that streamlines Java Persistence API (JPA) development, offering powerful commands and interactive UI components for generating entities, attributes, and relationships directly within Java files, among other functionalities.

The plugin mainly aims to replicate the advanced functionalities of modern JPA development tools, bringing those capabilities seamlessly to Neovim. This effort seeks to attract Java developers back to Neovim by enabling an efficient and integrated workflow for JPA-centric tasks. It is a part of a series of plugins I'm working on, related to Java and Spring development.

**nvim-javagenie** utilizes a standalone Tree-sitter instance provided by Python in a virtual environment, rather than relying on Neovim’s built-in Tree-sitter support. This standalone setup allows precise control over syntax tree parsing and customization, enabling the plugin to execute advanced Tree-sitter queries and modifications unique to JPA code. By directly identifying and manipulating Java elements like annotations, relationships, and specific JPA patterns, nvim-javagenie ensures accurate and efficient handling of code without interference from Neovim’s default Tree-sitter configuration.

**It is still under development**.

I'll be slowly developing it. Feel free to contribute.

# Dependencies

The plugin depends on three Python libraries, which are installed in a virtual environment (venv):

- pynvim
- tree-sitter
- tree-sitter-java

For the TUI, it relies on **nui-components.nvim**, which also depends on **nui.nvim**.

**jdtls** should be properly configured on Neovim.

# Installation

## Lazy

```lua
{ 'andreluisos/nvim-javagenie',
  dependencies = {
    'grapp-dev/nui-components.nvim',
    'MunifTanjim/nui.nvim',
  }
}
```

## Packer

```lua
use {
  'andreluisos/nvim-javagenie',
  requires = {
    { 'grapp-dev/nui-components.nvim' },
    { 'MunifTanjim/nui.nvim' },
  }
}
```

# TODO

Among with bug fixing, I also plan to:

- [ ] Create DTO for an entity (WIP)
- [ ] Implement UI for JPA repository creation
- [x] Create Java files (enum, interface, annotation, class, record)
- [ ] Implement Spring Initializr and project loading
- [ ] Runner for Java applications
- [ ] Figure out a way to create tests
- [ ] Implement Entity attribute/relationship editing
- [ ] ![Port to Java?](https://github.com/andreluisos/nvim-jpagenie/issues/9)

Request new features in the ![**Issues**](https://github.com/andreluisos/nvim-jpagenie/issues) tab and I will check it out.

**Please**, also ![**report bugs**](https://github.com/andreluisos/nvim-jpagenie/issues) in the ![**Issues**](https://github.com/andreluisos/nvim-jpagenie/issues) tab. It's important.

# Features Overview

The plugin includes a range of features, each powered by dedicated Tree-sitter queries, to streamline common JPA tasks. These functionalities are aimed at giving Java developers a robust development experience within Neovim:

## Create a JPA Entity

![JPA Entity creation](https://github.com/andreluisos/nvim-jpagenie/blob/media/create_entity.gif)

## Easily add Entity attributes

- ID attributes
- Basic type attributes
- Enum type attributes

![Entity ID attribute creation](https://github.com/andreluisos/nvim-jpagenie/blob/media/create_id_attribute.gif)
![Entity basic attribute creation](https://github.com/andreluisos/nvim-jpagenie/blob/media/create_basic_attribute.gif)
![Entity enum attribute creation](https://github.com/andreluisos/nvim-jpagenie/blob/media/create_enum_attribute.gif)

## Quickly create Entity relationships

- Many-to-one relationships
- One-to-one relationships
- Many-to-one relationships with automatic equals() and hashCode() method generation

![Entity ID attribute creation](https://github.com/andreluisos/nvim-jpagenie/blob/media/create_many_to_one.gif)
![Entity basic attribute creation](https://github.com/andreluisos/nvim-jpagenie/blob/media/create_one_to_one.gif)
![Entity enum attribute creation](https://github.com/andreluisos/nvim-jpagenie/blob/media/create_many_to_many.gif)
