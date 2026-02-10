; ModuleID = 'program-b7eef4a0-4573-11f0-be85-773714bb7840'
source_filename = "program-b7eef4a0-4573-11f0-be85-773714bb7840"

define void @main() #0 {
entry:
  call void @__quantum__rt__initialize(ptr null)
  call void @__quantum__qis__h__body(ptr null)
  call void @__quantum__qis__h__body(ptr inttoptr (i64 1 to ptr))
  call void @__quantum__qis__h__body(ptr inttoptr (i64 2 to ptr))
  call void @__quantum__qis__h__body(ptr inttoptr (i64 3 to ptr))
  call void @__quantum__qis__mz__body(ptr null, ptr inttoptr (i64 4 to ptr))
  call void @__quantum__qis__mz__body(ptr inttoptr (i64 1 to ptr), ptr inttoptr (i64 5 to ptr))
  call void @__quantum__qis__mz__body(ptr inttoptr (i64 2 to ptr), ptr inttoptr (i64 6 to ptr))
  call void @__quantum__qis__mz__body(ptr inttoptr (i64 3 to ptr), ptr inttoptr (i64 7 to ptr))
  call void @__quantum__qis__reset__body(ptr null)
  call void @__quantum__qis__reset__body(ptr inttoptr (i64 1 to ptr))
  call void @__quantum__qis__reset__body(ptr inttoptr (i64 2 to ptr))
  call void @__quantum__qis__reset__body(ptr inttoptr (i64 3 to ptr))
  %0 = call i1 @__quantum__qis__read_result__body(ptr inttoptr (i64 4 to ptr))
  br i1 %0, label %then, label %else

then:                                             ; preds = %entry
  call void @__quantum__qis__x__body(ptr null)
  call void @__quantum__qis__cnot__body(ptr null, ptr inttoptr (i64 1 to ptr))
  %1 = call i1 @__quantum__qis__read_result__body(ptr inttoptr (i64 5 to ptr))
  br i1 %1, label %then1, label %else2

else:                                             ; preds = %entry
  br label %continue

continue:                                         ; preds = %else, %continue3
  %2 = call i1 @__quantum__qis__read_result__body(ptr null)
  br i1 %2, label %then4, label %else5

then1:                                            ; preds = %then
  call void @__quantum__qis__cnot__body(ptr inttoptr (i64 1 to ptr), ptr inttoptr (i64 2 to ptr))
  br label %continue3

else2:                                            ; preds = %then
  br label %continue3

continue3:                                        ; preds = %else2, %then1
  br label %continue

then4:                                            ; preds = %continue
  call void @__quantum__qis__cnot__body(ptr inttoptr (i64 2 to ptr), ptr inttoptr (i64 3 to ptr))
  call void @__quantum__qis__h__body(ptr inttoptr (i64 2 to ptr))
  br label %continue6

else5:                                            ; preds = %continue
  br label %continue6

continue6:                                        ; preds = %else5, %then4
  call void @__quantum__rt__result_record_output(ptr null, ptr null)
  call void @__quantum__rt__result_record_output(ptr inttoptr (i64 1 to ptr), ptr null)
  call void @__quantum__rt__result_record_output(ptr inttoptr (i64 2 to ptr), ptr null)
  call void @__quantum__rt__result_record_output(ptr inttoptr (i64 3 to ptr), ptr null)
  ret void
}

declare void @__quantum__rt__initialize(ptr)

declare void @__quantum__qis__h__body(ptr)

declare void @__quantum__qis__mz__body(ptr, ptr writeonly) #1

declare void @__quantum__qis__reset__body(ptr)

declare i1 @__quantum__qis__read_result__body(ptr)

declare void @__quantum__qis__x__body(ptr)

declare void @__quantum__qis__cnot__body(ptr, ptr)

declare void @__quantum__rt__result_record_output(ptr, ptr)

attributes #0 = { "entry_point" "output_labeling_schema" "qir_profiles"="base" "required_num_qubits"="4" "required_num_results"="8" }
attributes #1 = { "irreversible" }

!llvm.module.flags = !{!0, !1, !2, !3}

!0 = !{i32 1, !"qir_major_version", i32 2}
!1 = !{i32 7, !"qir_minor_version", i32 0}
!2 = !{i32 1, !"dynamic_qubit_management", i1 false}
!3 = !{i32 1, !"dynamic_result_management", i1 false}
