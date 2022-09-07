;;; blobber-mode.el --- Description -*- lexical-binding: t; -*-
;;
;; Copyright (C) 2022 Daniel Nagy
;;
;; Author: Daniel Nagy <danielnagy@posteo.de>
;; Maintainer: Daniel Nagy <danielnagy@posteo.de>
;; Created: July 27, 2022
;; Modified: July 27, 2022
;; Version: 0.0.1
;; Keywords:
;; Homepage: https://github.com/nagy/blobber-mode
;; Package-Requires: ((emacs "24.3"))
;;
;; This file is not part of GNU Emacs.
;;
;;; Commentary:
;;
;;  Description
;;
;;; Code:

(require 'magit)
(require 'blobber)
(require 'consult)

(defvar-local blobber-mode-identifier nil "Buffer-local object holding an `nix-store-path` object.")

(cl-defun blobber-mode-insert-identifier ()
  "Insert a section showing the size of STORE-PATH."
  (magit-insert-section (identifier "ident")
    (magit-insert-heading
      (propertize (format "%-12s" "Identifier:") 'face 'magit-section-heading)
      blobber-mode-identifier)))

(cl-defun blobber-mode-insert-hash ()
  "Insert a section showing the size of STORE-PATH."
  (magit-insert-section (hash "hash")
    (magit-insert-heading
      (propertize (format "%-12s" "Hash:") 'face 'magit-section-heading)
      (blobber--hash))))

(cl-defun blobber-mode-insert-name ()
  "Insert a section showing the size of STORE-PATH."
  (magit-insert-section (name "name")
    (magit-insert-heading
      (propertize (format "%-12s" "Name:") 'face 'magit-section-heading)
      (blobber--name))))

(cl-defun blobber-mode-insert-size ()
  "Insert a section showing the size of STORE-PATH."
  (magit-insert-section (identifier "size")
    (magit-insert-heading
      (propertize (format "%-12s" "Size:") 'face 'magit-section-heading)
      (format "%s"
              (blobber-size blobber-mode-identifier)))))

(cl-defun blobber-mode-insert-tvf-found ()
  "Insert a section showing the tvf-found of STORE-PATH."
  (magit-insert-section (tvf-found "tvf-found")
    (magit-insert-heading
      (propertize (format "%-12s" "tvf-found:") 'face 'magit-section-heading)
      (format "%s" (when (blobber--get-tvf) t)))))

(cl-defun blobber-mode-insert-mime ()
  "Insert a section showing the tvf-found of STORE-PATH."
  (magit-insert-section (mime "mime")
    (magit-insert-heading
      (propertize (format "%-12s" "Mime:") 'face 'magit-section-heading)
      (format "%s" (mailcap-file-name-to-mime-type blobber-mode-identifier)))))

(defcustom blobber-mode-headers-hook
  '(;; blobber-mode-insert-identifier
    blobber-mode-insert-hash
    blobber-mode-insert-name
    blobber-mode-insert-size
    blobber-mode-insert-tvf-found
    blobber-mode-insert-mime)
  "Hook run to insert headers into the blobber-mode buffer.
A list of functions."
  :type 'hook)

(defun blobber-show (identifier)
  (interactive (list (consult--read (blobber-list) :prompt "blobber hash> ")))
  (switch-to-buffer (format "Blobber: %s" identifier))
  (blobber-mode)
  (setq-local blobber-mode-identifier identifier)
  (setq-local blobber--hash identifier)
  (setq-local list-buffers-directory (blobber--hash))
  (let ((inhibit-read-only t))
    (erase-buffer)
    (magit-insert-section (blobber)
      (magit-insert-headers 'blobber-mode-headers-hook))
    (current-buffer)))

(defun blobber--hash ()
  (substring blobber--hash 0 32))

(defun blobber--name ()
  (substring blobber--hash 33))

;;;###autoload
(defun blobber-bookmark-jump (bm)
  "Jump to the blobber bookmark BM."
  (interactive (list (read-from-minibuffer "Bookmark: ")))
  (blobber-show (bookmark-prop-get bm 'filename)))
(put 'blobber-bookmark-jump 'bookmark-handler-type "Blobber")

(defun blobber--bookmark-make-record-function ()
  "A function to be used as `bookmark-make-record-function'."
  `(,(concat "blobber: " blobber--hash)
     (handler . blobber-bookmark-jump )
     (filename . ,blobber--hash)))

(defun blobber--get-tvf ()
  (car (blobber-find (concat (blobber--hash) ".tvf"))))

(defun blobber--find-tvf ()
  (interactive)
  (if-let ((found (blobber--get-tvf)))
      (blobber-show found)
      (user-error "Blobber: tvf not found")))

(defun blobber--find-file-this ()
  (interactive)
  (find-file (concat "~/.local/share/blobber/" blobber-mode-identifier)))

(define-derived-mode blobber-mode magit-section-mode "Blobber"
  "Blobber mode."
  :interactive nil
  (setq-local
   bookmark-make-record-function #'blobber--bookmark-make-record-function)
  (read-only-mode 1))

(map! :map blobber-mode-map :localleader "t" #'blobber--find-tvf)
(map! :map blobber-mode-map :localleader "f" #'blobber--find-file-this)

(provide 'blobber-mode)
;;; blobber-mode.el ends here
