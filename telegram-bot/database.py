import os
import aiosqlite
from config import DB_PATH, DIAMOND_PACKAGES


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                game_id TEXT NOT NULL,
                server_id TEXT NOT NULL,
                nickname TEXT,
                diamonds INTEGER NOT NULL,
                price INTEGER NOT NULL,
                product_id TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                proof_file_id TEXT,
                status TEXT DEFAULT 'pending',
                smileone_order_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS packages (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                diamonds INTEGER NOT NULL,
                price INTEGER NOT NULL,
                active INTEGER DEFAULT 1
            )
        """)
        await db.commit()
        await _seed_packages(db)


async def _seed_packages(db: aiosqlite.Connection):
    async with db.execute("SELECT COUNT(*) FROM packages") as cursor:
        count = (await cursor.fetchone())[0]
    if count == 0:
        await db.executemany(
            "INSERT INTO packages (id, product_id, diamonds, price) VALUES (?, ?, ?, ?)",
            [(p["id"], p["product_id"], p["diamonds"], p["price"]) for p in DIAMOND_PACKAGES],
        )
        await db.commit()


async def get_packages(active_only: bool = True) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM packages"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY diamonds ASC"
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def set_package_price(pkg_id: str, new_price: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE packages SET price = ? WHERE id = ?", (new_price, pkg_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def set_package_active(pkg_id: str, active: bool) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE packages SET active = ? WHERE id = ?", (1 if active else 0, pkg_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def create_order(order_data: dict) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO orders (order_id, user_id, username, game_id, server_id,
                nickname, diamonds, price, product_id, payment_method)
            VALUES (:order_id, :user_id, :username, :game_id, :server_id,
                :nickname, :diamonds, :price, :product_id, :payment_method)
        """, order_data)
        await db.commit()
    return order_data["order_id"]


async def update_order(order_id: str, updates: dict):
    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    set_clause += ", updated_at = CURRENT_TIMESTAMP"
    updates["order_id"] = order_id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE orders SET {set_clause} WHERE order_id = :order_id",
            updates
        )
        await db.commit()


async def get_order(order_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE order_id = ?", (order_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_user_orders(user_id: int, limit: int = 5) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_pending_orders() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at ASC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def search_orders_by_game_id(game_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE game_id = ? ORDER BY created_at DESC",
            (game_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_all_user_ids() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT DISTINCT user_id FROM orders ORDER BY user_id"
        ) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT status, COUNT(*) FROM orders GROUP BY status"
        ) as cur:
            status_counts = {row[0]: row[1] for row in await cur.fetchall()}

        async with db.execute("""
            SELECT COALESCE(SUM(price), 0) FROM orders
            WHERE status = 'completed'
            AND date(created_at) = date('now', 'localtime')
        """) as cur:
            today_revenue = (await cur.fetchone())[0]

        async with db.execute("""
            SELECT COUNT(*) FROM orders
            WHERE date(created_at) = date('now', 'localtime')
        """) as cur:
            today_orders = (await cur.fetchone())[0]

        async with db.execute("""
            SELECT COALESCE(SUM(price), 0) FROM orders
            WHERE status = 'completed'
            AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now', 'localtime')
        """) as cur:
            month_revenue = (await cur.fetchone())[0]

        async with db.execute("""
            SELECT COUNT(*) FROM orders
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now', 'localtime')
        """) as cur:
            month_orders = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT COALESCE(SUM(price), 0) FROM orders WHERE status = 'completed'"
        ) as cur:
            total_revenue = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM orders"
        ) as cur:
            total_customers = (await cur.fetchone())[0]

        async with db.execute("""
            SELECT diamonds, COUNT(*) as cnt FROM orders
            WHERE status = 'completed'
            GROUP BY diamonds ORDER BY cnt DESC LIMIT 5
        """) as cur:
            popular = await cur.fetchall()

    return {
        "status_counts": status_counts,
        "today_revenue": today_revenue,
        "today_orders": today_orders,
        "month_revenue": month_revenue,
        "month_orders": month_orders,
        "total_revenue": total_revenue,
        "total_customers": total_customers,
        "popular_packages": popular,
    }
