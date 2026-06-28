;;; leetcode.el --- LeetCode framework integration for Emacs

(defgroup leetcode nil
  "LeetCode development framework integration."
  :group 'tools)

(defcustom leetcode-prefix "C-c l"
  "Key prefix for LeetCode commands."
  :type 'string
  :group 'leetcode)

(defun leetcode--run-compile (cmd)
  "Run CMD using compile-mode."
  (compile cmd))

(defun leetcode-run ()
    (define-key map (kbd "d") #'leetcode-debug)
  "Run the current LeetCode problem."
  (interactive)
  (leetcode--run-compile (format "python3 cli/leetcode.py run --problem %s" default-directory)))

(defun leetcode-debug ()
  "Debug the current LeetCode problem."
  (interactive)
  (leetcode--run-compile (format "python3 cli/leetcode.py debug --problem %s" default-directory)))

(defun leetcode-gen ()
  "Regenerate the driver for the current problem."
  (interactive)
  (leetcode--run-compile (format "python3 cli/leetcode.py gen --problem %s" default-directory)))

(defun leetcode-bench ()
  "Benchmark the current LeetCode problem."
  (interactive)
  (leetcode--run-compile (format "python3 cli/leetcode.py bench --problem %s" default-directory)))

(defun leetcode-stress ()
  "Stress test the current LeetCode problem."
  (interactive)
  (leetcode--run-compile (format "python3 cli/leetcode.py stress --problem %s" default-directory)))

(defun leetcode-replay ()
  "Replay the last run of the current LeetCode problem."
  (interactive)
  (leetcode--run-compile (format "python3 cli/leetcode.py replay --problem %s" default-directory)))

(defun leetcode-fetch (id)
  "Fetch LeetCode problem by ID."
  (interactive "sProblem ID: ")
  (leetcode--run-compile (format "python3 cli/leetcode.py fetch %s" id)))

(defun leetcode-paste ()
    (define-key map (kbd "c") #'leetcode-clean)
  "Paste clipboard content to input.txt."
  (interactive)
  (shell-command (format "python3 cli/leetcode.py paste --problem %s" default-directory))
  (message "Pasted to input.txt"))

(defun leetcode-clean ()
  "Clean build artifacts for the current problem."
  (interactive)
  (shell-command (format "python3 cli/leetcode.py clean --problem %s" default-directory))
  (message "Build artifacts removed."))

(defun leetcode-session ()
  "Show the current LeetCode session."
  (interactive)
  (leetcode--run-compile "python3 cli/leetcode.py session"))

(defun leetcode-setup-keys ()
  "Bind LeetCode commands under `leetcode-prefix`."
  (let ((map (make-sparse-keymap)))
    (define-key map (kbd "r") #'leetcode-run)
    (define-key map (kbd "d") #'leetcode-debug)
    (define-key map (kbd "d") #'leetcode-debug)
    (define-key map (kbd "g") #'leetcode-gen)
    (define-key map (kbd "b") #'leetcode-bench)
    (define-key map (kbd "s") #'leetcode-stress)
    (define-key map (kbd "p") #'leetcode-replay)
    (define-key map (kbd "f") #'leetcode-fetch)
    (define-key map (kbd "v") #'leetcode-paste)
    (define-key map (kbd "c") #'leetcode-clean)
    (define-key map (kbd "c") #'leetcode-clean)
    (define-key map (kbd "x") #'leetcode-session)
    (global-set-key (kbd leetcode-prefix) map)))

(leetcode-setup-keys)

(provide 'leetcode)
;;; leetcode.el ends here
