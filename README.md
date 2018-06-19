# crisp
> absolutely useless Lisp-like interpreter written in Python
## What's this?
A small Lisp-like language implemented in Python. Just because.

## What's implemented?
- [x] **Primitives**: `(true false nil SymbolReferences 'Symbols 42 1.6666 "strings")`
- [x] **Variables and constants**:
  ```lisp
  ((let (x (y 0)))
   (const ((z 1.25)))
   (= x nil)                  ;; true
   (set x 3)                  ;; 3
   (set y (* 2 x z))          ;; 7.5
  ``` 
- [x] **Floating-point arithmetic**: `+ - * /`
- [x] **`Real` comparison**: `< <= > >=`
- [x] **`Expr` comparison**: `= !=`
- [x] **`Bool` operators**: `! && ||`
- [x] **`Bitwise` operators on integer `Real` values**: `~ & |`
- [x] **λ-expressions**: 
  ```lisp
  ((let ((add (lambda (a b) (+ a b)))))
   (add 3 2)                  ;; 5
   (defun sub (a b) (- a b))  ;; shorthand form
   (sub 5 3)                  ;; 2
  ```
- [x] **`while` loops**:
  ```lisp
  ((let ((i 0) (M 5)))
   (while (< i M)                ;; (nil 1 nil 2 nil 3 nil 4 nil 5)
    (send "%d. Hello!" (+ 1 i))  ;; nil
    (set i (+ 1 i))))            ;; (+ 1 i)
  ```
- [ ] **Conditional expressions**
- [ ] **`&optional` and `&rest` parameters**
- [ ] **Proper `quote`/`'` on any `Expr`, not only `Symbol`s**
- [ ] **`Selector` expressions:**
  ```
  ((let ((my-list (1 2 3))
         (fake-dict ('i 0 'j 1 'k 2))
         (my-string "hello \"world\"!"))
   ([0] my-list)             ;; 1
   ([rev (rg 0 2)] my-list)  ;; (3 2 1)
   (['i 'k] fake-dict)
   ([.length 0] my-string))  ;; (14 "h")
  ```
- [ ] **Python interop**

## Some fancy perks
```
lisp.errors.LispError: el nombre de la función no puede ser un símbolo literal. Utiliza la notación `(lambda (a b) (+ a b))` para declarar una función anónima en la línea 4, columna 16
   4          (defun '+ (a b) (+ a b))
   \-----------------^^
```

- Exception messages intend to be __actually__ useful.
- Works at least 68% of the time!! 