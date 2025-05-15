# student-performance-analysis-tool

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Overview

The **Student Performance Analysis Tool** is a web-based application designed to manage and analyze student academic and extracurricular performance. It provides role-based access for students, teachers, and administrators to track marks, attendance, and Student Activity Points (SAP) requests. Built with Flask and MySQL, this tool enables educational institutions to monitor student progress and streamline administrative tasks efficiently.

## Features

- **Role-Based Access**:
  - **Students**: View marks, attendance, SAP points, and submit SAP requests.
  - **Teachers**: Access student performance data and lists.
  - **Admins**: Manage users, students, subjects, marks, attendance, and SAP approvals.
- **Marks Management**: Record and visualize subject-wise marks with exam-type details.
- **Attendance Tracking**: Log and review subject-specific attendance records.
- **SAP System**: Submit and manage extracurricular activity points with proof links.
- **Performance Visualization**: Generate bar and line graphs for subject-wise analysis using Matplotlib.
- **Scalable Design**: Supports future enhancements like AI-driven analytics.

## Technologies Used

- **Backend**: Python 3.9+, Flask 2.0+
- **Database**: MySQL 8.0+
- **Database Connector**: PyMySQL
- **Frontend**: HTML, Jinja2 templates, Matplotlib (for performance graphs)
- **Development Environment**: Local setup with Python and MySQL (XAMPP optional)
- **Dependencies**: Listed in `requirements.txt`

## Prerequisites

- Python 3.9 or higher
- MySQL 8.0 or higher
- Git (for cloning the repository)
- (Optional) XAMPP or standalone MySQL for local database setup

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/SOLAIRAJ28/student-performance-analysis-tool.git
   cd student-performance-analysis-tool
