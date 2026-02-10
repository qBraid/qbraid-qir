; ModuleID = 'test_conditional_gates'
source_filename = "circuit-778bcda"

define void @main() #0 {
entry:
  call void @__quantum__rt__initialize(ptr null)
  call void @__quantum__qis__h__body(ptr null)
  call void @__quantum__qis__h__body(ptr inttoptr (i64 1 to ptr))
  %0 = call i1 @__quantum__qis__read_result__body(ptr inttoptr (i64 1 to ptr))
  br i1 %0, label %then, label %else

then:                                             ; preds = %entry
  call void @__quantum__qis__z__body(ptr inttoptr (i64 2 to ptr))
  br label %continue

else:                                             ; preds = %entry
  call void @__quantum__qis__x__body(ptr inttoptr (i64 2 to ptr))
  call void @__quantum__qis__x__body(ptr inttoptr (i64 2 to ptr))
  br label %continue

continue:                                         ; preds = %else, %then
  %1 = call i1 @__quantum__qis__read_result__body(ptr null)
  br i1 %1, label %then1, label %else2

then1:                                            ; preds = %continue
  call void @__quantum__qis__z__body(ptr inttoptr (i64 2 to ptr))
  br label %continue3

else2:                                            ; preds = %continue
  br label %continue3

continue3:                                        ; preds = %else2, %then1
  call void @__quantum__qis__mz__body(ptr null, ptr null)
  call void @__quantum__qis__mz__body(ptr inttoptr (i64 1 to ptr), ptr inttoptr (i64 1 to ptr))
  %2 = call i1 @__quantum__qis__read_result__body(ptr inttoptr (i64 1 to ptr))
  br i1 %2, label %then4, label %else5

then4:                                            ; preds = %continue3
  call void @__quantum__qis__rz__body(double 5.000000e-01, ptr inttoptr (i64 2 to ptr))
  br label %continue6

else5:                                            ; preds = %continue3
  call void @__quantum__qis__x__body(ptr inttoptr (i64 2 to ptr))
  call void @__quantum__qis__x__body(ptr inttoptr (i64 2 to ptr))
  br label %continue6

continue6:                                        ; preds = %else5, %then4
  %3 = call i1 @__quantum__qis__read_result__body(ptr null)
  br i1 %3, label %then7, label %else8

then7:                                            ; preds = %continue6
  call void @__quantum__qis__rz__body(double 5.000000e-01, ptr inttoptr (i64 2 to ptr))
  br label %continue9

else8:                                            ; preds = %continue6
  br label %continue9

continue9:                                        ; preds = %else8, %then7
  call void @__quantum__rt__result_record_output(ptr null, ptr null)
  call void @__quantum__rt__result_record_output(ptr inttoptr (i64 1 to ptr), ptr null)
  call void @__quantum__rt__result_record_output(ptr inttoptr (i64 2 to ptr), ptr null)
  ret void
}

declare void @__quantum__rt__initialize(ptr)

declare void @__quantum__qis__h__body(ptr)

declare i1 @__quantum__qis__read_result__body(ptr)

declare void @__quantum__qis__z__body(ptr)

declare void @__quantum__qis__x__body(ptr)

declare void @__quantum__qis__mz__body(ptr, ptr writeonly) #1

declare void @__quantum__qis__rz__body(double, ptr)

declare void @__quantum__rt__result_record_output(ptr, ptr)

attributes #0 = { "entry_point" "output_labeling_schema" "qir_profiles"="custom" "required_num_qubits"="3" "required_num_results"="3" }
attributes #1 = { "irreversible" }

!llvm.module.flags = !{!0, !1, !2, !3}

!0 = !{i32 1, !"qir_major_version", i32 1}
!1 = !{i32 7, !"qir_minor_version", i32 0}
!2 = !{i32 1, !"dynamic_qubit_management", i1 false}
!3 = !{i32 1, !"dynamic_result_management", i1 false}
