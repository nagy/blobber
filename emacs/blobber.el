;;; blobber.el --- Description -*- lexical-binding: t; -*-
;;
;; Copyright (C) 2022 Daniel Nagy
;;
;; Author: Daniel Nagy <danielnagy@posteo.de>
;; Maintainer: Daniel Nagy <danielnagy@posteo.de>
;; Created: July 25, 2022
;; Modified: July 25, 2022
;; Version: 0.0.1
;; Keywords: data files tools
;; Homepage: https://github.com/nagy/blobber
;; Package-Requires: ((emacs "24.3"))
;;
;; This file is not part of GNU Emacs.
;;
;;; Commentary:
;;
;;  Description
;;
;;; Code:

(defvar blobber-program "blobber" )

(defvar-local blobber--hash nil "the ref hash back")

(defvar blobber-writedir (expand-file-name "~/.local/share/blobber/"))

(defmacro blobber--process-string (&rest args)
  `(with-temp-buffer
     (let* ((inhibit-message t)
            (exitcode (call-process blobber-program nil t nil ,@args)))
       (if (zerop exitcode)
           (let ((result (string-remove-suffix "\n" (buffer-string))))
             (unless (string-empty-p result)
               result))
         (error (buffer-string))))))

(defmacro blobber--process-lines (&rest args)
  `(cl-remove-if #'string-empty-p
                 (split-string (or
                                (blobber--process-string ,@args)
                                "") "\n")))

(defun blobber-find (arg)
  (blobber--process-lines "find" arg))

(defun blobber-list ()
  (blobber--process-lines "ls"))

(defun blobber-cat (hash)
  (blobber--process-string "cat" hash))

(defun blobber-list-storage ()
  (blobber--process-lines "ls-storage"))

(defun blobber-hash-func (filename)
  (interactive "f")
  (blobber--process-string "hashfile" filename))

(defun blobber-put (filepath &optional name)
  (interactive "f")
  (blobber--process-string "put" filepath))

(defun blobber-stat (filename)
  (interactive "f")
  (json-parse-string
   (blobber--process-string "stat" filename)))

(defun blobber-size (filename)
  (interactive "f")
  (elt
   (blobber-stat filename)
   6))

(defun blobber-dired-jump ()
  (interactive)
  (dired blobber-writedir))

(defun blobber-dired-put ()
  (interactive)
  (cl-loop for file in (dired-get-marked-files)
           collect
           (blobber-put file)))

(defun blobber-dired-put-and-delete ()
  (interactive)
  (cl-loop for file in (dired-get-marked-files)
           collect
           (and
            (blobber-put file)
            (delete-file file)))
  (revert-buffer-without-query))

(defvar-keymap blobber-map
  :doc "Keymap for blobber."
  "p" #'blobber-put
  "f" #'blobber-file)

(defun blobber ()
  (interactive)
  (let* ((result (consult--read (blobber-list)
                                :prompt  "blobber hashes> "))
         (buf (generate-new-buffer (concat "Blobber: " result)))
         (content (blobber-cat result)))
    (switch-to-buffer buf)
    (insert content)
    (goto-char (point-min))
    (set-buffer-file-coding-system (set-auto-coding (downcase result) (buffer-size)))
    (set-auto-mode)
    (read-only-mode 1)
    (setq blobber--hash result)))

(provide 'blobber)
;;; blobber.el ends here
