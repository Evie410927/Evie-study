-- Evie-study 词库双端同步表。
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
