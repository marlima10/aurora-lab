<?php
declare(strict_types=1);

namespace Aurora\Database;

use PDO;

final class Migrator
{
    public function __construct(private PDO $db, private string $directory) {}

    public function run(): void
    {
        (new Transaction($this->db))->run(function (): void {
            $this->db->exec('CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)');
            $applied = $this->db->query('SELECT version FROM schema_migrations')->fetchAll(PDO::FETCH_COLUMN);
            $files = glob($this->directory . '/migrations/*.php');
            sort($files);
            foreach ($files as $file) {
                $version = basename($file, '.php');
                if (in_array($version, $applied, true)) {
                    continue;
                }
                $migrate = require $file;
                $migrate($this->db);
                $statement = $this->db->prepare('INSERT INTO schema_migrations (version, applied_at) VALUES (:version, :at)');
                $statement->execute([':version' => $version, ':at' => gmdate('c')]);
                // O seed inicial roda uma vez; não recria exercícios apagados em cada requisição.
                if ($version === '001_initial_schema') {
                    $seed = require $this->directory . '/seeds/exercises.php';
                    $seed($this->db);
                }
            }
        });
    }
}
