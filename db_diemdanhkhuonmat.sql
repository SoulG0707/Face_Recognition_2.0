-- Tạo cơ sở dữ liệu nếu chưa tồn tại
IF DB_ID('attendance_db') IS NULL
BEGIN
    CREATE DATABASE attendance_db;
END
GO

-- Sử dụng cơ sở dữ liệu
USE attendance_db;
GO

-- Tạo bảng students nếu chưa tồn tại
IF OBJECT_ID('students', 'U') IS NULL
BEGIN
    CREATE TABLE students (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(255), -- Giữ lại để lưu tên (có thể null nếu không cần)
        student_id NVARCHAR(50) NOT NULL UNIQUE, -- MSSV là duy nhất
        major NVARCHAR(255) NOT NULL
    );
END
GO

-- Nếu bảng students đã tồn tại, sửa để thêm ràng buộc UNIQUE cho student_id
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'student_id' 
    AND Object_ID = Object_ID(N'students') 
    AND is_nullable = 0
)
BEGIN
    ALTER TABLE students
    ALTER COLUMN student_id NVARCHAR(50) NOT NULL;
    
    ALTER TABLE students
    ADD CONSTRAINT UK_student_id UNIQUE (student_id);
END
GO

-- Nếu cột name trong students không cho phép null, sửa để cho phép null
IF EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'name' 
    AND Object_ID = Object_ID(N'students') 
    AND is_nullable = 0
)
BEGIN
    ALTER TABLE students
    ALTER COLUMN name NVARCHAR(255) NULL;
END
GO

-- Tạo bảng attendance nếu chưa tồn tại
IF OBJECT_ID('attendance', 'U') IS NULL
BEGIN
	CREATE TABLE attendance (
		id INT IDENTITY(1,1) PRIMARY KEY,
		student_id NVARCHAR(50) NOT NULL,
		major NVARCHAR(255) NOT NULL,
		date DATE NOT NULL,
		time TIME NOT NULL,
		emotion NVARCHAR(50) NULL
	);
END
GO

-- Nếu bảng attendance đã tồn tại và có cột name, xóa cột name
IF EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'name' 
    AND Object_ID = Object_ID(N'attendance')
)
BEGIN
    ALTER TABLE attendance
    DROP COLUMN name;
END
GO

-- Thêm dữ liệu mẫu
INSERT INTO students (name, student_id, major)
VALUES 
(N'Ngoc', '22205600', N'Artificial Intelligence'),
(N'Nhi', '22203891', N'Artificial Intelligence');
GO

-- Truy vấn dữ liệu
SELECT * FROM attendance;
SELECT * FROM students;

-- Xóa toàn bộ lần điểm danh
DELETE FROM attendance;

-- Reset ID tự tăng về 1
DBCC CHECKIDENT ('attendance', RESEED, 0);
GO