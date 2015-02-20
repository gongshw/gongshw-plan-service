PRAGMA foreign_keys = FALSE;

-- ----------------------------
--  Table structure for plan_meta
-- ----------------------------
CREATE TABLE IF NOT EXISTS "plan_meta" (
  "id"        TEXT    NOT NULL PRIMARY KEY,
  "unit"      INTEGER NOT NULL,
  "index"     INTEGER NOT NULL,
  "repeat"    INTEGER NOT NULL,
  "text"      TEXT    NOT NULL,
  "color"     TEXT NOT NULL,
  "sort"      REAL    NOT NULL,
  "add_at"    INTEGER NOT NULL,
  "delete_at" INTEGER
);

-- ----------------------------
--  Table structure for plan_record
-- ----------------------------
CREATE TABLE IF NOT EXISTS "plan_record" (
  "meta_id"   TEXT    NOT NULL,
  "index"     INTEGER NOT NULL,
  "finish_at" INTEGER NOT NULL,
  PRIMARY KEY ("meta_id", "index")
);


PRAGMA foreign_keys = TRUE;
