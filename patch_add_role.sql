ALTER TABLE public."user" ADD COLUMN IF NOT EXISTS role VARCHAR(20);
ALTER TABLE public."user" ALTER COLUMN role SET DEFAULT 'admin';
UPDATE public."user" SET role = 'admin' WHERE role IS NULL;
ALTER TABLE public."user" ALTER COLUMN role SET NOT NULL;
ALTER TABLE public."user" ALTER COLUMN role DROP DEFAULT;
