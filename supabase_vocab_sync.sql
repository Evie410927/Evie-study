-- Evie-study 词库与学习资料同步。
-- 词条保存在 vocab_items；资料元数据保存在 resource_files，二进制保存在私有 Storage bucket vocab-resources。
-- 在 Supabase Dashboard -> SQL Editor 中完整执行一次。

create table if not exists public.vocab_items (
  user_id uuid not null references auth.users(id) on delete cascade,
  language text not null check (language in ('kr', 'jp')),
  word_id text not null,
  payload jsonb not null default '{}'::jsonb,
  updated_at bigint not null default ((extract(epoch from now()) * 1000)::bigint),
  deleted_at bigint,
  primary key (user_id, language, word_id)
);

create index if not exists vocab_items_user_language_updated_idx
  on public.vocab_items (user_id, language, updated_at desc);

alter table public.vocab_items enable row level security;

drop policy if exists "Users can read their own vocabulary" on public.vocab_items;
create policy "Users can read their own vocabulary"
  on public.vocab_items
  for select
  to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "Users can insert their own vocabulary" on public.vocab_items;
create policy "Users can insert their own vocabulary"
  on public.vocab_items
  for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists "Users can update their own vocabulary" on public.vocab_items;
create policy "Users can update their own vocabulary"
  on public.vocab_items
  for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "Users can delete their own vocabulary" on public.vocab_items;
create policy "Users can delete their own vocabulary"
  on public.vocab_items
  for delete
  to authenticated
  using ((select auth.uid()) = user_id);

revoke all on table public.vocab_items from anon;
grant select, insert, update, delete on table public.vocab_items to authenticated;

create table if not exists public.resource_files (
  user_id uuid not null references auth.users(id) on delete cascade,
  language text not null default 'jp' check (language in ('kr', 'jp')),
  resource_id text not null,
  name text not null default '',
  mime_type text not null default 'application/octet-stream',
  size bigint not null default 0 check (size >= 0 and size <= 52428800),
  sha256 text not null default '',
  storage_path text not null default '',
  sort_order bigint not null default 0,
  order_updated_at bigint not null default 0,
  updated_at bigint not null default ((extract(epoch from now()) * 1000)::bigint),
  deleted_at bigint,
  primary key (user_id, language, resource_id)
);

alter table public.resource_files
  add column if not exists language text;

update public.resource_files
set language = 'jp'
where language is null or language not in ('kr', 'jp');

alter table public.resource_files
  alter column language set default 'jp',
  alter column language set not null;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conrelid = 'public.resource_files'::regclass
      and conname = 'resource_files_language_check'
  ) then
    alter table public.resource_files
      add constraint resource_files_language_check check (language in ('kr', 'jp'));
  end if;
end
$$;

alter table public.resource_files
  drop constraint if exists resource_files_pkey;

alter table public.resource_files
  add primary key (user_id, language, resource_id);

alter table public.resource_files
  add column if not exists sort_order bigint not null default 0;

alter table public.resource_files
  add column if not exists order_updated_at bigint not null default 0;

create index if not exists resource_files_user_updated_idx
  on public.resource_files (user_id, updated_at desc);

create index if not exists resource_files_user_sort_idx
  on public.resource_files (user_id, sort_order asc);

create index if not exists resource_files_user_language_updated_idx
  on public.resource_files (user_id, language, updated_at desc);

create index if not exists resource_files_user_language_sort_idx
  on public.resource_files (user_id, language, sort_order asc);

alter table public.resource_files enable row level security;

drop policy if exists "Users can read their own resources" on public.resource_files;
create policy "Users can read their own resources"
  on public.resource_files for select to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "Users can insert their own resources" on public.resource_files;
create policy "Users can insert their own resources"
  on public.resource_files for insert to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists "Users can update their own resources" on public.resource_files;
create policy "Users can update their own resources"
  on public.resource_files for update to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "Users can delete their own resources" on public.resource_files;
create policy "Users can delete their own resources"
  on public.resource_files for delete to authenticated
  using ((select auth.uid()) = user_id);

revoke all on table public.resource_files from anon;
grant select, insert, update, delete on table public.resource_files to authenticated;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'vocab-resources',
  'vocab-resources',
  false,
  52428800,
  array[
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
    'text/plain',
    'image/png',
    'image/jpeg',
    'image/webp'
  ]::text[]
)
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "Users can read their own resource objects" on storage.objects;
create policy "Users can read their own resource objects"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'vocab-resources'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

drop policy if exists "Users can insert their own resource objects" on storage.objects;
create policy "Users can insert their own resource objects"
  on storage.objects for insert to authenticated
  with check (
    bucket_id = 'vocab-resources'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

drop policy if exists "Users can update their own resource objects" on storage.objects;
create policy "Users can update their own resource objects"
  on storage.objects for update to authenticated
  using (
    bucket_id = 'vocab-resources'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  )
  with check (
    bucket_id = 'vocab-resources'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

drop policy if exists "Users can delete their own resource objects" on storage.objects;
create policy "Users can delete their own resource objects"
  on storage.objects for delete to authenticated
  using (
    bucket_id = 'vocab-resources'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );
